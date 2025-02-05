#!flask/bin/python
from flask import Flask, jsonify,Response,json,render_template
from time import sleep
import time

import traceback
from werkzeug.wsgi import ClosingIterator

class AfterResponse:
    def __init__(self, app=None):
        self.callbacks = []
        if app:
            self.init_app(app)

    def __call__(self, callback):
        self.callbacks.append(callback)
        return callback

    def init_app(self, app):
        # install extension
        app.after_response = self

        # install middleware
        app.wsgi_app = AfterResponseMiddleware(app.wsgi_app, self)

    def flush(self):
        for fn in self.callbacks:
            try:
                fn()
            except Exception:
                traceback.print_exc()

class AfterResponseMiddleware:
    def __init__(self, application, after_response_ext):
        self.application = application
        self.after_response_ext = after_response_ext

    def __call__(self, environ, after_response):
        iterator = self.application(environ, after_response)
        try:
            return ClosingIterator(iterator, [self.after_response_ext.flush])
        except Exception:
            traceback.print_exc()
            return iterator





app = Flask(__name__)

AfterResponse(app)

@app.route('/inner')
def save_data():
    response =  jsonify({'tasks': tasks})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response
    pass

@app.after_response
def foo():
#     while True:
    try:
        print(str(time.time()))
    except:
      print("Error in foo")
    return





@app.route('/')
def index():
    return render_template('LiveDisplayPage.html')

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():


    try:
        # thread = Thread(target=foo)
#         thread.start()
        # return "OK"

    	# !return Response(json.dumps(appData), mimetype="application/json",
# 		!headers={"Content-disposition": "attachment"})

#CORS(app)
        tasks = [
            {
                'id': 1,
                'SwimmerName': u'Name1',
                'swmTimeing': time.time(),
                'myRank': 1
            },
            {
                'id': 2,
                'SwimmerName': u'Name2',
                'swmTimeing': u'22:33:44',
                'myRank': 2
            },
            {
                'id': 3,
                'SwimmerName': u'Name3',
                'swmTimeing': u'33:44:55',
                'myRank': 3
            },
            {
                'id': 4,
                'SwimmerName': u'Name4',
                'swmTimeing': u'44:55:66',
                'myRank': 1
            },
            {
                'id': 5,
                'SwimmerName': u'Name5',
                'swmTimeing': u'55:66:33',
                'myRank': 1
            },
        ]
        response =  jsonify({'tasks': tasks})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    except:

        print("do")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)