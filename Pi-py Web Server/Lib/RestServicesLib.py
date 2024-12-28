from flask import Flask, jsonify,Response,json,render_template
import threading
from Lib.StopwatchLib import StopTimerServicecls

class RestServicecls:
    data = 'foo'
    host_name = "0.0.0.0"
    port = 5002
    app = Flask(__name__)


    @app.route('/')
    def index():
        return render_template('LiveDisplayPage.html')


    # GET requests will be blocked
    @app.route('/json-example', methods=['POST'])
    def json_example():
        request_data = request.get_json()

        language = None
        framework = None
        python_version = None
        example = None
        boolean_test = None

        if request_data:
            if 'language' in request_data:
                language = request_data['language']

            if 'framework' in request_data:
                framework = request_data['framework']

            if 'version_info' in request_data:
                if 'python' in request_data['version_info']:
                    python_version = request_data['version_info']['python']

            if 'examples' in request_data:
                if (type(request_data['examples']) == list) and (len(request_data['examples']) > 0):
                    example = request_data['examples'][0]

            if 'boolean_test' in request_data:
                boolean_test = request_data['boolean_test']

            ReturnVal=''' The language value is: {}
                   The framework value is: {}
                   The Python version is: {}
                   The item at index 0 in the example list is: {}
                   The boolean value is: {}'''.format(language, framework, python_version, example, boolean_test)
        print (language)

             # !return Response(json.dumps(appData), mimetype="application/json",
    # 		!headers={"Content-disposition": "attachment"})
        response =  ReturnVal
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response




    @app.route('/todo/api/v1.0/tasks', methods=['GET'])
    def get_tasks():

        #CORS(app)
        tasks = [
            {
                'id': 1,
                'SwimmerName': u'Name1',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[1]),
                'myRank': 1
            },
            {
                'id': 2,
                'SwimmerName': u'Name2',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[2]),
                'myRank': 2
            },
            {
                'id': 3,
                'SwimmerName': u'Name3',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[3]),
                'myRank': 3
            },
            {
                'id': 4,
                'SwimmerName': u'Name4',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[4]),
                'myRank': 1
            },
            {
                'id': 5,
                'SwimmerName': u'Name5',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[5]),
                'myRank': 1
            },
        ]


            # !return Response(json.dumps(appData), mimetype="application/json",
    # 		!headers={"Content-disposition": "attachment"})
        response =  jsonify({'tasks': tasks})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response