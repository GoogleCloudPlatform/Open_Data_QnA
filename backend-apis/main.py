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


from flask import Flask, request, jsonify, render_template
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

from opendataqna import get_all_databases,get_kgq,generate_sql,embed_sql,get_response,get_results,Visualize


module_path = os.path.abspath(os.path.join('.'))
sys.path.append(module_path)


RUN_DEBUGGER = True
DEBUGGING_ROUNDS = 2 
LLM_VALIDATION = True
EXECUTE_FINAL_SQL = True
Embedder_model = 'vertex'
SQLBuilder_model = 'gemini-1.0-pro'
SQLChecker_model = 'gemini-1.0-pro'
SQLDebugger_model = 'gemini-1.0-pro'
num_table_matches = 5
num_column_matches = 10
table_similarity_threshold = 0.3
column_similarity_threshold = 0.3
example_similarity_threshold = 0.3
num_sql_matches = 3

app = Flask(__name__) 
cors = CORS(app, resources={r"/*": {"origins": "*"}})



@app.route("/available_databases", methods=["GET"])
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
async def embedSql():

    envelope = str(request.data.decode('utf-8'))
    envelope=json.loads(envelope)
    user_database=envelope.get('user_database')
    final_sql = envelope.get('generated_sql')
    user_question = envelope.get('user_question')

    embedded, invalid_response=await embed_sql(user_database,user_question,generate_sql)

    if not invalid_response:
        responseDict = { 
                        "ResponseCode" : 201, 
                        "Message" : "Example SQL has been accepted for embedding",
                        "Error":""
                        } 
        return jsonify(responseDict)
    else:
        responseDict = { 
                   "ResponseCode" : 500, 
                   "KnownDB" : "",
                   "Error":embedded
                   } 
        return jsonify(responseDict)




@app.route("/run_query", methods=["POST"])
def getSQLResult():
    
    envelope = str(request.data.decode('utf-8'))
    envelope=json.loads(envelope)

    user_database = envelope.get('user_database')
    final_sql = envelope.get('generated_sql')

    result_df,invalid_response=get_results(user_database,final_sql)
    if not invalid_response:
        responseDict = { 
                "ResponseCode" : 200, 
                "KnownDB" : result_df.to_json(orient='records'),
                "Error":""
                }

    else:
        responseDict = { 
                "ResponseCode" : 500, 
                "KnownDB" : "",
                "Error":result_df
                } 
    return jsonify(responseDict)




@app.route("/get_known_sql", methods=["POST"])
def getKnownSQL():
    print("Extracting the known SQLs from the example embeddings.")
    envelope = str(request.data.decode('utf-8'))
    envelope=json.loads(envelope)
    
    user_database = envelope.get('user_database')


    result,invalid_response=get_kgq(user_database)
    
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



@app.route("/generate_sql", methods=["POST"])
async def generateSQL():
  
    envelope = str(request.data.decode('utf-8'))
    #    print("Here is the request payload " + envelope)
    envelope=json.loads(envelope)

    user_question = envelope.get('user_question')
    user_database = envelope.get('user_database')
    final_sql,invalid_response = await generate_sql(user_question,
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
        responseDict = { 
                        "ResponseCode" : 200, 
                        "GeneratedSQL" : final_sql,
                        "Error":""
                        }
    else:
        responseDict = { 
                        "ResponseCode" : 500, 
                        "GeneratedSQL" : "",
                        "Error":final_sql
                        }          

    return jsonify(responseDict)


@app.route("/generate_viz", methods=["POST"])
async def generateViz():
    envelope = str(request.data.decode('utf-8'))
    # print("Here is the request payload " + envelope)
    envelope=json.loads(envelope)

    user_question = envelope.get('user_question')
    generated_sql = envelope.get('generated_sql')
    sql_results = envelope.get('sql_results')

    chart_js=''

    try:
        chart_js = Visualize.generate_charts(user_question,generated_sql,sql_results)
        responseDict = { 
        "ResponseCode" : 200, 
        "GeneratedChartjs" : chart_js,
        "Error":""
        }
        return jsonify(responseDict)

    except Exception as e:
        # util.write_log_entry("Cannot generate the Visualization!!!, please check the logs!" + str(e))
        responseDict = { 
                "ResponseCode" : 500, 
                "GeneratedSQL" : "",
                "Error":"Issue was encountered while generating the Google Chart, please check the logs!"  + str(e)
                } 
        return jsonify(responseDict)

@app.route("/summarize_results", methods=["POST"])
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
async def getNaturalResponse():
   envelope = str(request.data.decode('utf-8'))
   #print("Here is the request payload " + envelope)
   envelope=json.loads(envelope)
   
   user_question = envelope.get('user_question')
   user_database = envelope.get('user_database')
   
   final_sql,invalid_response = await generate_sql(user_question,
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

        result_df,invalid_response=get_results(user_database,final_sql)
        
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
                        "Error":final_sql
                        }

   return jsonify(responseDict)         
   
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))