from flask import Flask, request, jsonify, make_response
from models import OrderModel

flask_app = Flask(__name__)

@flask_app.route("/api/orders", methods=["POST", "OPTIONS"])
def api_create_order():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method == "POST": # The actual request following the preflight
        order = OrderModel.create(...) # Whatever.
        return _corsify_actual_response(jsonify(order.to_dict()))
    else:
        raise RuntimeError("Weird - don't know how to handle method {}".format(request.method))

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response