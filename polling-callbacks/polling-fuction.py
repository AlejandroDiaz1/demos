"""
functions-framework==3.*
"""

import functions_framework
from flask import jsonify
import time
import random

pipeline_states = {}

@functions_framework.http
def pipeline_api(request):
    path = request.path
    if path == "/api/v3/namespaces/DGP/apps":
        return list_apps()
    elif "/workflows/DataPipelineWorkflow/runs" in path:
        pipeline_name = path.split("/apps/")[1].split("/workflows")[0]
        return get_pipeline_status(pipeline_name)
    elif "/start" in path:
        pipeline_name = path.split("/apps/")[1].split("/start")[0]
        return start_pipeline(pipeline_name)
    else:
        return jsonify({"error": "Invalid endpoint"}), 404

def list_apps():
    apps = {
        "data": [
            {
                "name": f"dgp_load_w{str(i).zfill(3)}_v1",
                "type": "App",
                "description": "Data Pipeline Application",
                "version": f"version-{i}"
            } for i in range(1, 5)
        ]
    }
    return jsonify(apps)

def get_pipeline_status(pipeline_name):
    if pipeline_name not in pipeline_states:
        return jsonify({"data": []})
        
    state = pipeline_states[pipeline_name]
    current_time = time.time()
    elapsed_time = current_time - state['start_time']
    
    # After 60 seconds, return empty array to signal completion
    if elapsed_time >= 60:
        return jsonify({"data": []})
        
    data = [{
        "runid": state['run_id'],
        "startTime": state['start_time'],
        "endTime": current_time
    }]
    return jsonify({"data": data})

def start_pipeline(pipeline_name):
    run_id = f"run-{int(time.time())}"
    pipeline_states[pipeline_name] = {
        'run_id': run_id,
        'start_time': time.time()
    }
    return jsonify({
        "data": {
            "runid": run_id
        }
    })
