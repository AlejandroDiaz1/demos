import functions_framework
from flask import jsonify, make_response
from google.cloud import workflows_v1
from google.cloud.workflows import executions_v1
import logging
import time
import json
import os

WORKFLOW_NAME = "demo-wf-loop-execution"
PROJECT_ID = "ci-gestor-sandbox" 
LOCATION = "us-central1"

def validate_cities(cities):
    if not isinstance(cities, list):
        return False
    for city in cities:
        if not isinstance(city, dict) or 'name' not in city:
            return False
    return True

def execute_workflow(cities):
    execution_client = executions_v1.ExecutionsClient()
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/workflows/{WORKFLOW_NAME}"
    
    execution = execution_client.create_execution(
        parent=parent,
        execution={"argument": json.dumps({"cities": cities})}
    )
    
    backoff_delay = 1
    execution_finished = False
    
    while not execution_finished:
        execution_result = execution_client.get_execution(name=execution.name)
        execution_finished = execution_result.state != executions_v1.Execution.State.ACTIVE
        
        if not execution_finished:
            time.sleep(backoff_delay)
            backoff_delay *= 2  
        else:
            if execution_result.state == executions_v1.Execution.State.SUCCEEDED:
                return json.loads(execution_result.result)
            else:
                raise Exception(f"Workflow failed: {execution_result.error.message}")

@functions_framework.http
def process_weather_alerts(request):
   try:
    logging.info("Received request: %s", request.get_json())

    request_json = request.get_json(silent=True)
    if not request_json:
        return make_response(jsonify({"error": "No JSON data provided"}), 400)

    if 'cities' not in request_json:
        return make_response(jsonify({"error": "Missing 'cities' in request"}), 400)
        
    if not validate_cities(request_json['cities']):
        return make_response(jsonify({"error": "Invalid cities format"}), 400)
        
    if len(request_json['cities']) > 10:
        return make_response(jsonify({"error": "Maximum 10 cities allowed"}), 400)

    result = execute_workflow(request_json['cities'])
    return jsonify(result)

   except Exception as e:
    return make_response(jsonify({"error": str(e)}), 500)

