# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Deterministic checks for SQL before it is sent to a database engine.

SQL produced by an LLM is untrusted: prompt instructions such as "generate SELECT
queries only" are advice that a crafted question can talk the model out of. The check in
this module does not involve a model. It parses the statement and accepts it only when

* it is exactly one statement,
* that statement is a read-only query (SELECT, optionally with CTEs or set operations),
* every table it reads is registered for the caller's data source, and
* it calls none of the functions known to have side effects or to reach outside the
  database.

Anything that cannot be parsed, or is not understood, is rejected.

This is one layer. The database account used by the application should also be limited
to reading the tables it serves.
"""

import re
import unicodedata

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

BIGQUERY = "bigquery"
POSTGRES = "postgres"

# Statement kinds and clauses that write, lock, or change session state. A node of one of
# these types anywhere in the tree is refused, which covers data-modifying CTEs
# (WITH x AS (DELETE ... RETURNING *)), SELECT ... INTO and SELECT ... FOR UPDATE.
# `Command` is what sqlglot returns for statements it does not model.
_FORBIDDEN_NODE_NAMES = (
    "Insert", "Update", "Delete", "Merge", "Create", "Drop", "Alter", "AlterTable",
    "TruncateTable", "Command", "Into", "Lock", "Set", "Transaction", "Commit", "Rollback",
    "Copy", "Grant", "Revoke", "Use", "Pragma", "Execute", "Analyze", "Export", "LoadData",
    "Kill", "Comment", "Describe", "Show", "Cache", "Uncache", "Refresh",
)
_FORBIDDEN_NODES = tuple(
    getattr(exp, name) for name in _FORBIDDEN_NODE_NAMES if hasattr(exp, name)
)

# PostgreSQL functions that a plain SELECT can use to write, sleep, read server files,
# reach other servers, or run SQL passed as text. Matched on the lowercased name.
_POSTGRES_FORBIDDEN_FUNCTION_PREFIXES = ("pg_", "lo_", "dblink")
_POSTGRES_FORBIDDEN_FUNCTIONS = frozenset({"set_config", "nextval", "setval"})
_POSTGRES_FORBIDDEN_FUNCTION_INFIX = "_to_xml"  # query_to_xml('<sql>') and its family

# Table-valued functions that only generate rows.
_ALLOWED_TABLE_FUNCTIONS = frozenset({"generate_series", "exploding_generate_series"})

# PostgreSQL Unicode-escaped identifiers and strings: U&"pg\005fsleep" names pg_sleep.
# The parser does not decode them, so a name written this way would dodge the checks.
_POSTGRES_UNICODE_ESCAPE = re.compile(r"u&[\"']", re.IGNORECASE)


def _has_unusual_whitespace(statement):
    """True for characters the engines and the parser may not agree are whitespace.

    Only space, tab, LF and CRLF are accepted between tokens. A bare CR ends a line
    comment in PostgreSQL, form feed is whitespace there, and so on: accepting them would
    let text hide in what the parser takes for a comment or a single token.
    """
    for position, char in enumerate(statement):
        if char in " \t\n":
            continue
        if char == "\r":
            if statement[position + 1:position + 2] != "\n":
                return True
            continue
        if unicodedata.category(char) in ("Cc", "Cf", "Zs", "Zl", "Zp"):
            return True
    return False


def _dialect(source_type):
    return BIGQUERY if str(source_type).lower() == BIGQUERY else POSTGRES


def _identifier_name(identifier, dialect):
    """Returns the name the engine resolves an identifier to."""
    name = identifier.this
    if dialect == POSTGRES and not identifier.args.get("quoted"):
        # PostgreSQL folds unquoted identifiers to lower case; quoted ones are exact.
        return name.lower()
    return name


def _function_name(function):
    if isinstance(function, exp.Anonymous):
        # `.name` also unwraps a quoted name such as "pg_sleep"(1).
        return function.name.lower()
    return function.sql_name().lower()


def _top_level_ctes(root):
    """Returns the CTEs of the statement's own WITH clause and whether it is RECURSIVE."""
    with_clause = root.args.get("with_") or root.args.get("with")
    if with_clause is None:
        return [], False
    return list(with_clause.expressions), bool(with_clause.args.get("recursive"))


def _cte_name(cte, dialect):
    alias = cte.args.get("alias")
    identifier = alias.this if alias is not None else None
    if not isinstance(identifier, exp.Identifier):
        return None
    return _identifier_name(identifier, dialect)


def _check_table(table, visible_ctes, allowed_tables, dialect):
    """Returns an error for one table reference, or None when it may be read."""
    target = table.this
    if not isinstance(target, exp.Identifier):
        if isinstance(target, exp.Func) and _function_name(target) in _ALLOWED_TABLE_FUNCTIONS:
            return None
        return "Table functions are not permitted in the FROM clause."

    name = _identifier_name(target, dialect)
    schema_identifier = table.args.get("db")

    if schema_identifier is None:
        if table.args.get("catalog") is None and name in visible_ctes:
            return None
        return (f"Table '{name}' must be referenced with its schema or dataset, "
                "for example schema.table_name.")

    schema = _identifier_name(schema_identifier, dialect)
    if (schema, name) not in allowed_tables:
        return f"Table '{schema}.{name}' is not part of the selected data source."
    return None


def _check_tables(root, allowed_tables, dialect):
    # Only the statement's own WITH clause introduces names that are trusted as CTE
    # references. A CTE declared in a nested query is visible only inside that query, so
    # treating its name as known everywhere would let it mask a real table elsewhere.
    # Nested CTEs are therefore not recognised and a query relying on one is refused.
    ctes, recursive = _top_level_ctes(root)
    cte_names = [_cte_name(cte, dialect) for cte in ctes]
    all_cte_names = {name for name in cte_names if name}

    tables_inside_ctes = set()
    for position, cte in enumerate(ctes):
        # Without RECURSIVE a CTE sees only the CTEs declared before it. A reference to
        # its own name, or to a later CTE, resolves to a real table.
        visible = all_cte_names if recursive else {name for name in cte_names[:position] if name}
        for table in cte.find_all(exp.Table):
            tables_inside_ctes.add(id(table))
            error = _check_table(table, visible, allowed_tables, dialect)
            if error:
                return error

    for table in root.find_all(exp.Table):
        if id(table) in tables_inside_ctes:
            continue
        error = _check_table(table, all_cte_names, allowed_tables, dialect)
        if error:
            return error
    return None


def _check_functions(root, dialect):
    if dialect != POSTGRES:
        return None
    for function in root.find_all(exp.Func):
        name = _function_name(function)
        if (name in _POSTGRES_FORBIDDEN_FUNCTIONS
                or name.startswith(_POSTGRES_FORBIDDEN_FUNCTION_PREFIXES)
                or _POSTGRES_FORBIDDEN_FUNCTION_INFIX in name):
            return f"Function '{name}' is not permitted."
    return None


def check_read_only_query(sql, source_type, allowed_tables):
    """Decides whether a SQL string may be sent to the source database.

    Args:
        sql: The exact statement that would be executed.
        source_type: 'bigquery' for BigQuery. Anything else is treated as PostgreSQL,
            matching how the connectors are selected elsewhere in the code base.
        allowed_tables: Iterable of (schema_or_dataset, table_name) pairs registered for
            the caller's data source.

    Returns:
        (True, "") when the statement is an allowed read-only query, otherwise
        (False, reason). The reason is safe to show to the user and to feed back to the
        model that wrote the query.
    """
    if not isinstance(sql, str) or not sql.strip():
        return False, "Query must be a non-empty string."

    allowed = {(str(schema), str(table)) for schema, table in (allowed_tables or ())}
    if not allowed:
        return False, "No tables are registered for the selected data source."

    # Statements are separated by ';' in both engines. Refusing every ';' other than
    # trailing terminators guarantees a single statement without relying on the parser
    # agreeing with the engine about where a string or comment ends.
    statement = re.sub(r"[;\s]+$", "", sql.strip())
    if ";" in statement:
        return False, "Only a single SQL statement is permitted. Remove every ';' from the query."

    if _has_unusual_whitespace(statement):
        return False, "Query contains control characters or unusual whitespace."

    dialect = _dialect(source_type)
    if dialect == POSTGRES and _POSTGRES_UNICODE_ESCAPE.search(statement):
        return False, "Unicode escape syntax (U&'...' or U&\"...\") is not permitted."

    try:
        parsed = [node for node in sqlglot.parse(statement, read=dialect) if node is not None]
    except (SqlglotError, RecursionError):
        return False, f"Query could not be parsed as {dialect} SQL."

    if len(parsed) != 1:
        return False, "Only a single SQL statement is permitted."
    root = parsed[0]

    # Unwrap "(SELECT ...)" so that the WITH clause of the inner query counts as top level.
    while isinstance(root, exp.Subquery) and not _top_level_ctes(root)[0] and isinstance(root.this, exp.Query):
        root = root.this

    if not isinstance(root, exp.Query):
        return False, "Only read-only SELECT queries are permitted."

    for node in root.walk():
        if isinstance(node, _FORBIDDEN_NODES):
            return False, f"Only read-only SELECT queries are permitted ({type(node).__name__.upper()} found)."

    error = _check_tables(root, allowed, dialect) or _check_functions(root, dialect)
    if error:
        return False, error
    return True, ""
