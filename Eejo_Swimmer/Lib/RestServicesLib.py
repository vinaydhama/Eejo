from flask import Flask, jsonify,Response,json,render_template,request
import threading
from Lib.StopwatchLib import StopTimerServicecls
from Lib.SwimDataHolder import HeatDataDisplay,MeetHeaderDisplay
from Lib.JsonLib import JsonHelper
import requests,json
JSONFilePath= "/home/pks/Desktop/Eejo_Swimmer/Data/FirebaseJSONData.json"


# API For Setting Meet Headers to Display  -DONE
# API For Setting Heat Details to Swimmer Names & Swimmer timeings to Display -DONE
# API For Getting Swimmer timeings to Server -DONE
# API To load \static JSON File
# API to Update Static JSON File

# API For LiveDataChange
    # Set/ Reseting Latch
    # Feeding Manual Time
    # Setting Swim Status
    # Modifying




class RestServicecls:
    StopTimerServiceclsobj=StopTimerServicecls()
    data = 'foo'
    host_name = "0.0.0.0"
    port = 5002
    app = Flask(__name__)

    def GetNextHeatID(JSONFilePath):
        data= JsonHelper.GetJSONFromFile(JSONFilePath)
        # VCR TO BE DONE Check if any Request from Reffree Console
        HeatID, EventID= JsonHelper.GetNextHeatIDFromFile(data)
        return HeatID, EventID

    @app.route('/')
    def index():
        # Should have call for
        return render_template('LiveDisplayPage.html')

    # GET requests will be blocked
    @app.route('/SetEventDetails', methods=['POST'])
    def SetEventDetails():
       JsonHelper.GetJSONFromFile(JSONFilePath)
       return

    @app.route('/GetMeetHeader', methods=['GET'])
    def GetDisplayHeader():

        data= JsonHelper.GetJSONFromFile(JSONFilePath)
        MeetDetail=JsonHelper.GetMeetHeader(data)
        response =  jsonify({'MeetDetail': MeetDetail})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response


    @app.route('/GetMeetHeaders', methods=['POST'])
    def GetDisplayHeaders():

        data= JsonHelper.GetJSONFromFile(JSONFilePath)
        MeetDetail=JsonHelper.GetMeetHeader(data)
        response =  jsonify({'MeetDetail': MeetDetail})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response



    @app.route('/GetHeatHeader', methods=['GET'])
    def GetHeatHeader():
        HeatData =  StopTimerServicecls.heatDataDisplay
        HeatHeaderJson= {'eventID':HeatData.eventID, 'EventName' :HeatData.eventName, 'HeatID':HeatData.HeatID,'HeatID':HeatData.HeatID,
        'HeatStartTime':HeatData.HeatStartTime,'HeatEndTime':HeatData.HeatEndTime }

        response =  jsonify({'HeatDetails': HeatHeaderJson})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response


    @app.route('/SetLiveHeatCommands', methods=["GET"])
    def SetLiveHeatCommands():
            commandname = request.args.get('commandname')
            commandvalue = request.args.get('commandvalue')
#             json_dict = request.get_json()
            print(commandname + commandvalue)

            match commandname:
                case 'StartHeat':
                    StopTimerServicecls.ResetTimer()
                    StopTimerServicecls.StartLatch=commandvalue

                # case 1:
    #                 return "one"
    #             case 2:
    #                 return "two"
                case default:
                    print("at default")

#             if ( request_data["StartHeat"]==1):
#                 StopTimerServicecls.ResetTimer()
#                 StopTimerServicecls.StartLatch=1
#             elif (request_data["StartHeat"]==0):
#                 StopTimerServicecls.ResetTimer()
#                 StopTimerServicecls.StartLatch=0
#             elif (request_data["StartHeat"]==0):
#                 StopTimerServicecls.HeatStatus=TimerStatus.WaitBeforeLoad


#             for boardnum in range(0,len(request_data["BoardList"])):

#                 if (request_data["BoardList"][boardnum]["LatchStatus"]==0):
#                     StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=0
#                     StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=0
#                 elif(request_data["BoardList"][boardnum]["LatchStatus"]==1):
#                     StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=1

#                 if (request_data["BoardList"][boardnum]["SwimStatus"]!=-1):
#                     StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].swimerStatus=request_data["BoardList"][boardnum]["SwimStatus"]

#                 if (request_data["BoardList"][boardnum]["SwimTimings"]!=-1):
#                     StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].timerValue=request_data["BoardList"][boardnum]["SwimTimings"]



            response =  jsonify({'HeatDetails': "OK"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")

            return response



# GET requests will be blocked
    @app.route('/SetLiveHeatDetails', methods=['POST'])
    def SetLiveHeatDetails():
        request_data = request.get_json()
#        request_data=""
        print (request_data)
        url="http://192.168.0.101:5002/SetLiveHeatDetails"
        if ( request_data["StartHeat"]==1):
            StopTimerServicecls.ResetTimer()
            StopTimerServicecls.StartLatch=1
        elif (request_data["StartHeat"]==0):
            StopTimerServicecls.ResetTimer()
            StopTimerServicecls.StartLatch=0
        elif (request_data["StartHeat"]==0):
            StopTimerServicecls.HeatStatus=TimerStatus.WaitBeforeLoad


        for boardnum in range(0,len(request_data["BoardList"])):

            if (request_data["BoardList"][boardnum]["LatchStatus"]==0):
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=0
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=0
            elif(request_data["BoardList"][boardnum]["LatchStatus"]==1):
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=1

            if (request_data["BoardList"][boardnum]["SwimStatus"]!=-1):
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].swimerStatus=request_data["BoardList"][boardnum]["SwimStatus"]

            if (request_data["BoardList"][boardnum]["SwimTimings"]!=-1):
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].timerValue=request_data["BoardList"][boardnum]["SwimTimings"]

        return request_data
        response = requests.post(url, data=request_data,
        headers={'Content-Type': 'application/json'})
        return  response.content

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

#         print(HeatDatafromJSON)

        return str(HeatDataDisplay)

       #  except:
#             print("Error in setting Next Heat")


    @app.route('/LiveTimer', methods=['GET'])
    def LiveTimer():


# Convert JSON string to Python dictionary
        HeatData =  StopTimerServicecls.heatDataDisplay
        sjson=[]
        for board in HeatData.SwimerBoardDetails:
            sjson.append(json.dumps(board.__dict__) )

#         print (sjson)
        response =  jsonify({'Boards': sjson})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response