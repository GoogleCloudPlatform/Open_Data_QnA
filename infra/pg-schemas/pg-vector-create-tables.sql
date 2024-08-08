CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS table_details_embeddings(
    source_type VARCHAR(100) NOT NULL,
    user_grouping VARCHAR(100) NOT NULL,
    table_schema VARCHAR(1024) NOT NULL,
    table_name VARCHAR(1024) NOT NULL,
    content TEXT,
    embedding vector(768));

CREATE TABLE IF NOT EXISTS tablecolumn_details_embeddings(
    source_type VARCHAR(100) NOT NULL,
    user_grouping VARCHAR(100) NOT NULL,
    table_schema VARCHAR(1024) NOT NULL,
    table_name VARCHAR(1024) NOT NULL,
    column_name VARCHAR(1024) NOT NULL,
    content TEXT,
    embedding vector(768));

CREATE TABLE IF NOT EXISTS example_prompt_sql_embeddings(
    user_grouping VARCHAR(1024) NOT NULL,
    example_user_question text NOT NULL,
    example_generated_sql text NOT NULL,
    embedding vector(768));
