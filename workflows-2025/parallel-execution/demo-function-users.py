# pip install functions-framework==3.*

import functions_framework

@functions_framework.http
def get_user(request):
    """Cloud Function to get user data."""
    
    # Simulated database of users
    users = {
        "1": {"name": "Alice", "email": "alice@example.com"},
        "2": {"name": "Bob", "email": "bob@example.com"}
    }

    # Extract user_id from the request
    request_args = request.args
    user_id = request_args.get('user_id') if request_args else None

    if user_id and user_id in users:
        return users[user_id], 200
    else:
        return {"error": "User not found"}, 404
