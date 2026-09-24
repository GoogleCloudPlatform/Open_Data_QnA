# -*- coding: utf-8 -*-


# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from flask import Flask, request, jsonify, render_template, Response
import asyncio
from collections.abc import Callable
import logging as log
import json
import datetime
import urllib
import re
import time
import textwrap
import pandas as pd
from flask_cors import CORS
import os
import sys
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps

firebase_admin.initialize_app()

from opendataqna import get_all_databases,get_kgq,generate_sql,embed_sql,get_response,get_results,visualize


module_path = os.path.abspath(os.path.join('.'))
sys.path.append(module_path)


def _verify_auth_header():
    header = request.headers.get("Authorization", None)
    if not header:
        return Response(status=401, response="Missing Authorization header"), None
    parts = header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return Response(status=401, response="Invalid Authorization header format. Expected 'Bearer <token>'"), None
    token = parts[1]
    try:
        decoded_token = firebase_admin.auth.verify_id_token(token)
        return None, decoded_token.get("uid")
    except Exception as e:
        log.exception(e)
        return Response(status=403, response=f"Error with authentication: {e}"), None


def jwt_authenticated(func: Callable[..., int]) -> Callable[..., int]:
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_decorated_function(*args, **kwargs):
            auth_response, uid = _verify_auth_header()
            if auth_response is not None:
                return auth_response
            request.uid = uid
            return await func(*args, **kwargs)
        return async_decorated_function
    else:
        @wraps(func)
        def sync_decorated_function(*args, **kwargs):
            auth_response, uid = _verify_auth_header()
            if auth_response is not None:
                return auth_response
            request.uid = uid
            return func(*args, **kwargs)
        return sync_decorated_function


FORBIDDEN_SQL_PATTERNS = [
    r"\bDROP\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
]


def is_safe_query(sql: str) -> tuple[bool, str]:
    """Validates that a SQL query is read-only and free of destructive statements."""
    if not sql or not isinstance(sql, str):
        return False, "Query must be a non-empty string"
    # Strip comments and surrounding whitespace
    cleaned = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL).strip()
    # Remove markdown code fences if present
    cleaned = cleaned.replace("```sql", "").replace("```", "").strip()

    # Check for forbidden DDL / DML keywords
    for pattern in FORBIDDEN_SQL_PATTERNS:
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            return False, f"Prohibited SQL operation detected: {match.group(0)}"

    # Check that it starts with allowed read-only keywords (SELECT, WITH, EXPLAIN)
    if not re.match(r"^(SELECT|WITH|EXPLAIN)\b", cleaned, re.IGNORECASE):
        return False, "Only read-only SELECT, WITH, or EXPLAIN queries are permitted"

    return True, ""


def is_valid_user_grouping(user_grouping: str) -> bool:
    """Validates that a user_grouping identifier is safe and matches standard naming."""
    if not user_grouping or not isinstance(user_grouping, str):
        return False
    return bool(re.match(r'^[a-zA-Z0-9_\-\.]{1,128}$', user_grouping.strip()))

RUN_DEBUGGER = True
DEBUGGING_ROUNDS = 2 
LLM_VALIDATION = False
EXECUTE_FINAL_SQL = True
Embedder_model = 'vertex'
SQLBuilder_model = 'gemini-1.5-pro'
SQLChecker_model = 'gemini-1.5-pro'
SQLDebugger_model = 'gemini-1.5-pro'
num_table_matches = 5
num_column_matches = 10
table_similarity_threshold = 0.3
column_similarity_threshold = 0.3
example_similarity_threshold = 0.3
num_sql_matches = 3

app = Flask(__name__) 
cors = CORS(app, resources={r"/*": {"origins": "*"}})



@app.route("/available_databases", methods=["GET"])
@jwt_authenticated
def getBDList():

    result,invalid_response=get_all_databases()
    
    if not invalid_response:
        responseDict = { 
                "ResponseCode" : 200, 
                "KnownDB" : result,
                "Error":""
                }

    else:
        responseDict = { 
                "ResponseCode" : 500, 
                "KnownDB" : "",
                "Error":result
                } 
    return jsonify(responseDict)




@app.route("/embed_sql", methods=["POST"])
@jwt_authenticated
async def embedSql():

    envelope = str(request.data.decode('utf-8'))
    envelope=json.loads(envelope)
    user_grouping=envelope.get('user_grouping')
    generated_sql = envelope.get('generated_sql')
    user_question = envelope.get('user_question')
    session_id = envelope.get('session_id')

    if not is_valid_user_grouping(user_grouping):
        return jsonify({
            "ResponseCode": 400,
            "KnownDB": "",
            "SessionID": session_id,
            "Error": "Invalid user_grouping format. Must be an alphanumeric identifier."
        }), 400

    if not user_question or not isinstance(user_question, str) or not user_question.strip():
        return jsonify({
            "ResponseCode": 400,
            "KnownDB": "",
            "SessionID": session_id,
            "Error": "Invalid or missing user_question."
        }), 400

    if not generated_sql or not isinstance(generated_sql, str) or not generated_sql.strip():
        return jsonify({
            "ResponseCode": 400,
            "KnownDB": "",
            "SessionID": session_id,
            "Error": "Invalid or missing generated_sql."
        }), 400

    is_safe, error_reason = is_safe_query(generated_sql)
    if not is_safe:
        return jsonify({
            "ResponseCode": 400,
            "KnownDB": "",
            "SessionID": session_id,
            "Error": f"Query rejected: {error_reason}"
        }), 400

    embedded, invalid_response=await embed_sql(session_id,user_grouping,user_question,generated_sql)

    if not invalid_response:
        responseDict = { 
                        "ResponseCode" : 201, 
                        "Message" : "Example SQL has been accepted for embedding",
                        "SessionID" : session_id,
                        "Error":""
                        } 
        return jsonify(responseDict)
    else:
        responseDict = { 
                   "ResponseCode" : 500, 
                   "KnownDB" : "",
                   "SessionID" : session_id,
                   "Error":embedded
                   } 
        return jsonify(responseDict)




@app.route("/run_query", methods=["POST"])
@jwt_authenticated
def getSQLResult():
    
    envelope = str(request.data.decode('utf-8'))
    envelope=json.loads(envelope)

    user_question = envelope.get('user_question')
    user_grouping = envelope.get('user_grouping')
    generated_sql = envelope.get('generated_sql')
    session_id = envelope.get('session_id')

    if not is_valid_user_grouping(user_grouping):
        return jsonify({
            "ResponseCode": 400,
            "KnownDB": "",
            "NaturalResponse": "",
            "SessionID": session_id,
            "Error": "Invalid user_grouping format. Must be an alphanumeric identifier."
        }), 400

    is_safe, error_reason = is_safe_query(generated_sql)
    if not is_safe:
        return jsonify({
            "ResponseCode": 400,
            "KnownDB": "",
            "NaturalResponse": "",
            "SessionID": session_id,
            "Error": f"Query rejected: {error_reason}"
        }), 400

    result_df,invalid_response=get_results(user_grouping,generated_sql)


    if not invalid_response:
        _resp,invalid_response=get_response(session_id,user_question,result_df.to_json(orient='records'))
        if not invalid_response:
            responseDict = { 
                    "ResponseCode" : 200, 
                    "KnownDB" : result_df.to_json(orient='records'),
                    "NaturalResponse" : _resp,
                    "SessionID" : session_id,
                    "Error":""
                    }
        else:
            responseDict = { 
                    "ResponseCode" : 500, 
                    "KnownDB" : result_df.to_json(orient='records'),
                    "NaturalResponse" : _resp,
                    "SessionID" : session_id,
                    "Error":""
                    }

    else:
        _resp=result_df
        responseDict = { 
                "ResponseCode" : 500, 
                "KnownDB" : "",
                "NaturalResponse" : _resp,
                "SessionID" : session_id,
                "Error":result_df
                } 
    return jsonify(responseDict)




@app.route("/get_known_sql", methods=["POST"])
@jwt_authenticated
def getKnownSQL():
    print("Extracting the known SQLs from the example embeddings.")
    envelope = str(request.data.decode('utf-8'))
    envelope=json.loads(envelope)
    
    user_grouping = envelope.get('user_grouping')

    if not is_valid_user_grouping(user_grouping):
        return jsonify({
            "ResponseCode": 400,
            "KnownSQL": "",
            "Error": "Invalid user_grouping format. Must be an alphanumeric identifier."
        }), 400

    result,invalid_response=get_kgq(user_grouping)
    
    if not invalid_response:
        responseDict = { 
                "ResponseCode" : 200, 
                "KnownSQL" : result,
                "Error":""
                }

    else:
        responseDict = { 
                "ResponseCode" : 500, 
                "KnownSQL" : "",
                "Error":result
                } 
    return jsonify(responseDict)



@app.route("/generate_sql", methods=["POST"])
@jwt_authenticated
async def generateSQL():
    print("Here is the request payload ")
    envelope = str(request.data.decode('utf-8'))
    print("Here is the request payload " + envelope)
    envelope=json.loads(envelope)

    user_question = envelope.get('user_question')
    user_grouping = envelope.get('user_grouping')
    session_id = envelope.get('session_id')
    user_id = envelope.get('user_id')

    if not is_valid_user_grouping(user_grouping):
        return jsonify({
            "ResponseCode": 400,
            "GeneratedSQL": "",
            "SessionID": session_id,
            "Error": "Invalid user_grouping format. Must be an alphanumeric identifier."
        }), 400

    generated_sql,session_id,invalid_response = await generate_sql(session_id,
                user_question,
                user_grouping,  
                RUN_DEBUGGER,
                DEBUGGING_ROUNDS, 
                LLM_VALIDATION,
                Embedder_model,
                SQLBuilder_model,
                SQLChecker_model,
                SQLDebugger_model,
                num_table_matches,
                num_column_matches,
                table_similarity_threshold,
                column_similarity_threshold,
                example_similarity_threshold,
                num_sql_matches,
                user_id=user_id)

    if not invalid_response:
        responseDict = { 
                        "ResponseCode" : 200, 
                        "GeneratedSQL" : generated_sql,
                        "SessionID" : session_id,
                        "Error":""
                        }
    else:
        responseDict = { 
                        "ResponseCode" : 500, 
                        "GeneratedSQL" : "",
                        "SessionID" : session_id,
                        "Error":generated_sql
                        }          

    return jsonify(responseDict)


@app.route("/generate_viz", methods=["POST"])
@jwt_authenticated
async def generateViz():
    envelope = str(request.data.decode('utf-8'))
    # print("Here is the request payload " + envelope)
    envelope=json.loads(envelope)

    user_question = envelope.get('user_question')
    generated_sql = envelope.get('generated_sql')
    sql_results = envelope.get('sql_results')
    session_id = envelope.get('session_id')
    chart_js=''

    try:
        chart_js, invalid_response = visualize(session_id,user_question,generated_sql,sql_results)
        
        if not invalid_response:
            responseDict = { 
            "ResponseCode" : 200, 
            "GeneratedChartjs" : chart_js,
            "Error":"",
            "SessionID":session_id
            }
        else:
            responseDict = { 
                "ResponseCode" : 500, 
                "GeneratedSQL" : "",
                "SessionID":session_id,
                "Error": chart_js
                } 


        return jsonify(responseDict)

    except Exception as e:
        # util.write_log_entry("Cannot generate the Visualization!!!, please check the logs!" + str(e))
        responseDict = { 
                "ResponseCode" : 500, 
                "GeneratedSQL" : "",
                "SessionID":session_id,
                "Error":"Issue was encountered while generating the Google Chart, please check the logs!"  + str(e)
                } 
        return jsonify(responseDict)

@app.route("/summarize_results", methods=["POST"])
@jwt_authenticated
async def getSummary():
    envelope = str(request.data.decode('utf-8'))
    envelope=json.loads(envelope)
   
    user_question = envelope.get('user_question')
    sql_results = envelope.get('sql_results')

    result,invalid_response=get_response(user_question,sql_results)
    
    if not invalid_response:
        responseDict = { 
                    "ResponseCode" : 200, 
                    "summary_response" : result,
                    "Error":""
                    } 

    else:
        responseDict = { 
                    "ResponseCode" : 500, 
                    "summary_response" : "",
                    "Error":result
                    } 
    return jsonify(responseDict)




@app.route("/natural_response", methods=["POST"])
@jwt_authenticated
async def getNaturalResponse():
   envelope = str(request.data.decode('utf-8'))
   #print("Here is the request payload " + envelope)
   envelope=json.loads(envelope)
   
   user_question = envelope.get('user_question')
   user_grouping = envelope.get('user_grouping')

   if not is_valid_user_grouping(user_grouping):
       return jsonify({
           "ResponseCode": 400,
           "summary_response": "",
           "Error": "Invalid user_grouping format. Must be an alphanumeric identifier."
       }), 400
   
   generated_sql,session_id,invalid_response = await generate_sql(user_question,
                user_grouping,  
                RUN_DEBUGGER,
                DEBUGGING_ROUNDS, 
                LLM_VALIDATION,
                Embedder_model,
                SQLBuilder_model,
                SQLChecker_model,
                SQLDebugger_model,
                num_table_matches,
                num_column_matches,
                table_similarity_threshold,
                column_similarity_threshold,
                example_similarity_threshold,
                num_sql_matches)
   
   if not invalid_response:

        result_df,invalid_response=get_results(user_grouping,generated_sql)
        
        if not invalid_response:
            result,invalid_response=get_response(user_question,result_df.to_json(orient='records'))

            if not invalid_response:
                responseDict = { 
                            "ResponseCode" : 200, 
                            "summary_response" : result,
                            "Error":""
                            } 

            else:
                responseDict = { 
                            "ResponseCode" : 500, 
                            "summary_response" : "",
                            "Error":result
                            } 


        else:
            responseDict = { 
                    "ResponseCode" : 500, 
                    "KnownDB" : "",
                    "Error":result_df
                    } 

   else:
        responseDict = { 
                        "ResponseCode" : 500, 
                        "GeneratedSQL" : "",
                        "Error":generated_sql
                        }

   return jsonify(responseDict)   


@app.route("/get_results", methods=["POST"])
@jwt_authenticated
async def getResultsResponse():
   envelope = str(request.data.decode('utf-8'))
   #print("Here is the request payload " + envelope)
   envelope=json.loads(envelope)
   
   user_question = envelope.get('user_question')
   user_database = envelope.get('user_database')

   if not is_valid_user_grouping(user_database):
       return jsonify({
           "ResponseCode": 400,
           "GeneratedResults": "",
           "Error": "Invalid user_database format. Must be an alphanumeric identifier."
       }), 400
   
   generated_sql,invalid_response = await generate_sql(user_question,
                user_database,  
                RUN_DEBUGGER,
                DEBUGGING_ROUNDS, 
                LLM_VALIDATION,
                Embedder_model,
                SQLBuilder_model,
                SQLChecker_model,
                SQLDebugger_model,
                num_table_matches,
                num_column_matches,
                table_similarity_threshold,
                column_similarity_threshold,
                example_similarity_threshold,
                num_sql_matches)
   
   if not invalid_response:

        result_df,invalid_response=get_results(user_database,generated_sql)
        
        if not invalid_response:
            responseDict = { 
                            "ResponseCode" : 200, 
                            "GeneratedResults" : result_df.to_json(orient='records'),
                            "Error":""
                            } 

        else:
            responseDict = { 
                    "ResponseCode" : 500, 
                    "GeneratedResults" : "",
                    "Error":result_df
                    } 

   else:
        responseDict = { 
                        "ResponseCode" : 500, 
                        "GeneratedResults" : "",
                        "Error":generated_sql
                        }

   return jsonify(responseDict)  
   
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))