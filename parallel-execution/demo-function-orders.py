# pip install functions-framework==3.*

import functions_framework

@functions_framework.http
def get_order(request):
    """Cloud Function to get order details."""
    
    # Simulated database of orders
    orders = {
        "101": {"item": "Laptop", "price": 1200},
        "102": {"item": "Headphones", "price": 150}
    }

    # Extract order_id from the request
    request_args = request.args
    order_id = request_args.get('order_id') if request_args else None

    if order_id and order_id in orders:
        return orders[order_id], 200
    else:
        return {"error": "Order not found"}, 404