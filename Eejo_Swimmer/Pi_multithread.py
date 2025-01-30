from flask import Flask, jsonify,Response,json,render_template
import threading
from time import sleep
import time

data = 'foo'
host_name = "0.0.0.0"
port = 5001
app = Flask(__name__)

@app.route("/")
def main():
    return data

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

#if __name__ == "__main__":


threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=False, use_reloader=False)).start()

while True:
    print( time.time())
    sleep(0.01)