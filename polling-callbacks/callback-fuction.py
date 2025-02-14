"""
functions-framework==3.*
flask==2.*
google-cloud-workflows==1.12.0
google-auth==2.22.0
google-auth-httplib2==0.1.0
"""

from google.cloud.workflows import executions_v1
from google.auth import default
from google.auth.transport.requests import AuthorizedSession
import functions_framework
import json

PROJECT_ID = ''
LOCATION = ''
WORKFLOW_ID = ''

@functions_framework.http
def handle_request(request):
    path = request.path.strip('/')
    return trigger_workflow() if path == 'trigger' else handle_approval(request) if path == 'approve' else ('Invalid path', 404)

def trigger_workflow():
    try:
        client = executions_v1.ExecutionsClient()
        parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/workflows/{WORKFLOW_ID}"
        
        execution = executions_v1.Execution()
        execution.argument = json.dumps({})
        
        request = executions_v1.CreateExecutionRequest(
            parent=parent,
            execution=execution
        )
        
        response = client.create_execution(request=request)
        return {
            "execution_id": response.name.split('/')[-1],
            "message": "Workflow started successfully"
        }
    
    except Exception as e:
        print(f"Error starting workflow: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

def handle_approval(request):
    try:
        callback_url = request.args.get('callback_url')
        action = request.args.get('action')
        
        if not callback_url or action not in ['approve', 'reject']:
            return {"error": "Invalid parameters"}, 400
        
        # Get authenticated session
        credentials, _ = default()
        authed_session = AuthorizedSession(credentials)
        
        # Send authenticated request
        response = authed_session.post(
            callback_url,
            json={'approved': action == 'approve'},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            return {"status": "success", "message": f"Successfully sent {action} signal"}
        
        return {
            "status": "error", 
            "message": f"Callback failed with status {response.status_code}"
        }, response.status_code
            
    except Exception as e:
        print(f"Error in approval: {str(e)}")
        return {"status": "error", "message": str(e)}, 500
