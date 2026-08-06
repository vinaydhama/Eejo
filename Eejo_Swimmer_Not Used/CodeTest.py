from flask import Flask, jsonify,Response,json,render_template,request
import threading
from Lib.StopwatchLib import StopTimerServicecls
from Lib.SwimDataHolder import HeatDataDisplay
#eventholder= EventHolder()

SetStartTimercmd=0

class RestServicecls:
    data = 'foo'
    host_name = "0.0.0.0"
    port = 5002
    app = Flask(__name__)

# API For Setting Meet Headers to Display
# API For Setting Heat Details to Swimmer Names & Swimmer timeings to Display
# API For Getting Swimmer timeings to Server
# API To load \static JSON File
# API to Update Static JSON File

    @app.route('/')
    def index():
        # Should have call for
        return render_template('LiveDisplayPage.html')

    # GET requests will be blocked
    @app.route('/SetEventDetails', methods=['POST'])
    def SetEventDetails():
        #try:
       #  request_data = request.get_json()
#         eventData= eventJSONDecoder(request_data)
#         x= eventData.HeatList[0]
#         print (x)
#         heatdetails=  eventJSONDecoder(x)
#         print (heatdetails)
#         eventID = request_data['eventID']
#         eventName = request_data['eventName']
#         eventAddress = request_data['eventAddress']

#         eventholder.eventID=eventID
#         eventholder.eventName=eventName
#         eventholder.eventAddress=eventAddress

#         return '''
#                The eventID value is: {}, The eventName value is: {},The eventAddress value is: {}
#                '''.format(eventData.eventID,eventData,eventAddress)
        return

    @app.route('/SetDisplayHeader', methods=['GET'])
    def SetDisplayHeader():

        return
 # GET requests will be blocked
    @app.route('/SetNextHeatDetails', methods=['POST'])
    def SetNextHeatDetails():

        request_data = request.get_json()

        HeatDatafromJSON= eventJSONDecoder(request_data)
        HeatDataDisplay.MeetName = request_data['MeetName']
        HeatDataDisplay.MeetDate = request_data['MeetDate']
        HeatDataDisplay.MeetAddress = request_data['MeetAddress']
        HeatDataDisplay.eventName = request_data['eventName']
        HeatDataDisplay.HeatStartTime = request_data['HeatStartTime']
        HeatDataDisplay.HeatEndTime = request_data['HeatEndTime']

        #heatBoardDetailsList =  eventJSONDecoder(HeatDatafromJSON.heatBoardDetailsList)
        print(HeatDatafromJSON)
        #BoardDatafromJSON= HeatDatafromJSON.heatBoardDetailsList
        #print (eventJSONDecoder(BoardDatafromJSON))
       # HeatDataDisplay.heatBoardDetailsList=  eventJSONDecoder(BoardDatafromJSON)



#             x= eventData.HeatList[0]
#             print (x)
#             heatdetails=  eventJSONDecoder(x)
#             print (heatdetails)
#             eventID = request_data['eventID']
#             eventName = request_data['eventName']
#             eventAddress = request_data['eventAddress']

#             eventholder.eventID=eventID
#             eventholder.eventName=eventName
#             eventholder.eventAddress=eventAddress

        return str(HeatDataDisplay)

       #  except:
#             print("Error in setting Next Heat")




    ##GET requests will be blocked
#     @app.route('/json-example', methods=['POST'])
#     def json_example():
#         request_data = request.get_json()

#         language = request_data['eventID']
#         framework = request_data['framework']

        ##two keys are needed because of the nested object
#         python_version = request_data['version_info']['python']

        ##an index is needed because of the array
#         example = request_data['examples'][0]

#         boolean_test = request_data['boolean_test']

#         return '''
#                The language value is: {}
#                The framework value is: {}
#                The Python version is: {}
#                The item at index 0 in the example list is: {}
#                The boolean value is: {}'''.format(language, framework, python_version, example, boolean_test)


    @app.route('/LiveTimer', methods=['GET'])
    def get_tasks():

        #CORS(app)
        tasks = [
            {
                'id': 1,
                'SwimmerName': u'Name1',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.SwimerBoardDetails[1].timerValues),
                'myRank': 1
            },
            {
                'id': 2,
                'SwimmerName': u'Name2',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.SwimerBoardDetails[2].timerValues),
                'myRank': 2
            },
            {
                'id': 3,
                'SwimmerName': u'Name3',
                'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.SwimerBoardDetails[3].timerValues),
                'myRank': 3
            }
            #,
            # {
#                 'id': 4,
#                 'SwimmerName': u'Name4',
#                 'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.SwimerBoardDetails[4].timerValues),
#                 'myRank': 1
#             },
#             {
#                 'id': 5,
#                 'SwimmerName': u'Name5',
#                 'swmTimeing': StopTimerServicecls.time_convert(StopTimerServicecls.SwimerBoardDetails[5].timerValues),
#                 'myRank': 1
#             },
        ]


            # !return Response(json.dumps(appData), mimetype="application/json",
    # 		!headers={"Content-disposition": "attachment"})
        response =  jsonify({'tasks': tasks})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response