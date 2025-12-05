from flask import Flask, jsonify,Response,json,render_template,request
import threading
from Lib.StopwatchLib import StopTimerServicecls
from Lib.SwimDataHolder import HeatDataDisplay,MeetHeaderDisplay
from Lib.JsonLib import JsonHelper
import requests,json
from Lib.SwimDataHolder import TimerStatus,SwimerBoardDetail,Changeinfo
from Lib.FirebaseHelper import FireBaseHelper
from pathlib import Path
import os
import time
import socket
from Lib.ModbusLib import ModbusLibcls


#JSONFilePath= "/home/pks/Desktop/Eejo_Swimmer/Data/FirebaseJSONData.json"


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
    InitStatus=0
    data = 'foo'
    host_name = "0.0.0.0"
    port = 5002
    app = Flask(__name__)
    NextSetHeatID="WaitingToStart"
    AutoFindHeat=1
    TimerState=""
    TimerStateMessage=""
    Synced_JSONData=None
    hostIP=""


    
    @app.route('/SetUpdateSettings', methods=['GET'])
    def SetUpdateSettings():
        print("Hello")


    @app.route('/getAvailableHeatNames', methods=['GET'])
    def getAvailableHeatNames():
        parentpath = os.path.dirname(Path(__file__).parent.absolute())
        HeatsDirPath = os.path.join(parentpath,"Data","Heats")
        HeatFiles=[]
        for file in os.listdir(HeatsDirPath):
            if file.endswith(".EejoHeat"):
                HeatFiles.append(file)

        response =  jsonify({'HeatFiles': HeatFiles})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

            
    def ReadHeatFromLocalDisk( HeatFileDiskpath):
        return FireBaseHelper.GetJSONFromFile(HeatFileDiskpath)

    # For Passing File Content for JS Window
    def ReadHeatFromLocalFile(HeatFileName):
        parentpath = os.path.dirname(Path(__file__).parent.absolute())
        HeatFileName = os.path.join(parentpath,"Data","Heats",HeatFileName)
        return FireBaseHelper.GetJSONFromFile(HeatFileName)

    # For Passing File to Timer and to load Content for JS Window 
    # Not used 'InitTimerFromLocalFile' does same.
    def LoadHeatFromLocalFile(HeatFileName):
        parentpath = os.path.dirname(Path(__file__).parent.absolute())
        HeatFileName = os.path.join(parentpath,"Data","Heats",HeatFileName)
        FireBaseHelper.FirebaseJsonData=FireBaseHelper.GetJSONFromFile(HeatFileName)
        return FireBaseHelper.FirebaseJsonData


    # @app.route('/SaveHeatFileToLocalFile', methods=['GET'])
    # Used For Saving Modified Heat From JS to Timer
    def SaveHeatFileToLocalFile(HeatData,FileNametoSave):
        # HeatDateReceived = request.args.get('HeatData')
        # FileNametoSave = request.args.get('FileNametoSave')
        HeatDateToWrite = json.loads(HeatData)
        parentpath = os.path.dirname(Path(__file__).parent.absolute())
        HeatFilepathToSave = os.path.join(parentpath,"Data","Heats",FileNametoSave)

        FireBaseHelper.CreateifFiledontExists(HeatFilepathToSave)

        with open(HeatFilepathToSave, 'w+') as f:
            json.dump(HeatDateToWrite, f)

        # Write incoming JSON to File.
        response =  jsonify({'SaveHeatFileToLocalFile': "OK"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
#     # Not used
#     def SyncDataWithPreviousHeatResult(FileNameToSync):
#         # HeatData
#         PreviousLocalResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FileNameToSync)
#         JSONData= FireBaseHelper.SyncFileWithpreviousResults(FireBaseHelper.FirebaseJsonData,PreviousLocalResultData)
#     # Not used
#     def SyncDataWithPreviousSwimmerResult(JSONData,FileNameToSync):
#         # SwimmerData
#         FireBaseHelper.SyncFirebasefullSwDatawithlatestResults(JSONData,FileNameToSync)
#         FireBaseHelper.StartSyncingfullData(JSONData,FireBaseHelper.FirebaseJsonData)
#   # Not used
#     def initDataFromLocalDB(FileName):
#         StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart
#         FireBaseHelper.DownloadFirebaseToLocal(URLToSync+FireBaseHelper.strjson,FireBaseHelper.FirebaseJSONFilePath)
    def GetRestIP():

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            print(s.getsockname()[0])        
            RestServicecls.hostIP=s.getsockname()[0]        
            s.close()            
        except Exception as ex:
            print (ex)
            RestServicecls.hostIP="0.0.0.0"       
        
        return  RestServicecls.hostIP

    
    def LoadDataFromLocalFile(FileNametoRead,OverWriteOption=0, HeatFilepathToRead=""):
        StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart
        parentpath = os.path.dirname(Path(__file__).parent.absolute())
        if (HeatFilepathToRead==""):
            HeatFilepathToRead = os.path.join(parentpath,"Data","Heats",FileNametoRead)

        if (OverWriteOption==0): # Replace Dont Keep backup
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.WriteHeatResultsPath)
            
            FireBaseHelper.CopyHeatFile(HeatFilepathToRead,FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            # PreviousLocalResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            # Synced_JSONData= FireBaseHelper.SyncFileWithpreviousResults(FireBaseHelper.FirebaseJsonData,PreviousLocalResultData)

            #Clear all Files
        elif(OverWriteOption==1): # Replace Keep backup
            parentpath = os.path.dirname(Path(__file__).parent.absolute())
            s=time.gmtime()
            FirebaseJSONFilePath = os.path.join(parentpath,"Backup","FirebaseJSONData_Local_"  + time.strftime("%Y_%m_%d_%H_%M_%S", s) +".json")
            FirebaseSwimmerTable = os.path.join(parentpath,"Backup","FirebaseSwimmerTable_"  + time.strftime("%Y_%m_%d_%H_%M_%S", s) +".json")
            WriteHeatResultsPath= os.path.join(parentpath,"Backup","HeatExecutionResult_"  + time.strftime("%Y_%m_%d_%H_%M_%S", s) +".json")

            FireBaseHelper.CopyHeatFile(FireBaseHelper.FirebaseJSONFilePath,FirebaseJSONFilePath)
            FireBaseHelper.CopyHeatFile(FireBaseHelper.FirebaseSwimmerTable,FirebaseSwimmerTable)
            FireBaseHelper.CopyHeatFile(FireBaseHelper.WriteHeatResultsPath,WriteHeatResultsPath)

            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.WriteHeatResultsPath)

            FireBaseHelper.CopyHeatFile(HeatFilepathToRead,FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)

        elif(OverWriteOption==2): # Dont Replace But Sync
            FireBaseHelper.CopyHeatFile(HeatFilepathToRead,FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            PreviousLocalResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            Synced_JSONData= FireBaseHelper.SyncFileWithpreviousResults(Synced_JSONData,PreviousLocalResultData)
            
        RestServicecls.InitStatus=0
        RestServicecls.Synced_JSONData=Synced_JSONData
        return Synced_JSONData

    def LoaDataFromFirebaseData(URLToSync,OverWriteOption=0):
        StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart
        if (OverWriteOption==0): # Replace Dont Keep backup
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.WriteHeatResultsPath)

            FireBaseHelper.DownloadFirebaseToLocal(URLToSync+FireBaseHelper.strjson,FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            # PreviousLocalResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            # Synced_JSONData= FireBaseHelper.SyncFileWithpreviousResults(,PreviousLocalResultData)

            #Clear all Files
        elif(OverWriteOption==1): # Replace Keep backup
            parentpath = os.path.dirname(Path(__file__).parent.absolute())
            s=time.gmtime()
            FirebaseJSONFilePath = os.path.join(parentpath,"Backup","FirebaseJSONData_Local_"  + time.strftime("%Y_%m_%d_%H_%M_%S", s) +".json")
            FirebaseSwimmerTable = os.path.join(parentpath,"Backup","FirebaseSwimmerTable_"  + time.strftime("%Y_%m_%d_%H_%M_%S", s) +".json")
            WriteHeatResultsPath= os.path.join(parentpath,"Backup","HeatExecutionResult_"  + time.strftime("%Y_%m_%d_%H_%M_%S", s) +".json")


            FireBaseHelper.CopyHeatFile(FireBaseHelper.FirebaseJSONFilePath,FirebaseJSONFilePath)
            FireBaseHelper.CopyHeatFile(FireBaseHelper.FirebaseSwimmerTable,FirebaseSwimmerTable)
            FireBaseHelper.CopyHeatFile(FireBaseHelper.WriteHeatResultsPath,WriteHeatResultsPath)

            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.FirebaseSwimmerTable)
            FireBaseHelper.DeleteHeatFile(FireBaseHelper.WriteHeatResultsPath)

            FireBaseHelper.DownloadFirebaseToLocal(URLToSync+FireBaseHelper.strjson,FireBaseHelper.FirebaseJSONFilePath)
            Synced_JSONData = FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)

        elif(OverWriteOption==2): # Dont Replace But Sync
            FireBaseHelper.DownloadFirebaseToLocal(URLToSync+FireBaseHelper.strjson,FireBaseHelper.FirebaseJSONFilePath)
            PreviousLocalResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            Synced_JSONData= FireBaseHelper.SyncFileWithpreviousResults(FireBaseHelper.FirebaseJsonData,PreviousLocalResultData)

        RestServicecls.Synced_JSONData=Synced_JSONData
        RestServicecls.InitStatus=0
        return Synced_JSONData

# Notused
    # def LoaDataFromLocalData():
    #     StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart

    def InitTimerStart():
        try:
            #init Timer
            StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart
            FireBaseHelper.FirebaseJsonData=FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            FireBaseHelper.EventBaseurl=FireBaseHelper.Eventurl + FireBaseHelper.FirebaseJsonData["MeetName"]
            FireBaseHelper.SwimmerTable= FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseSwimmerTable)
            PreviousLocalResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            Synced_JSONData= FireBaseHelper.SyncFileWithpreviousResults(FireBaseHelper.FirebaseJsonData,PreviousLocalResultData)
            #FireBaseHelper.SyncFirebasefullSwDatawithlatestResults(Synced_JSONData,FireBaseHelper.SwimmerTable)
            #For Syncing All Main Data to Firebase
            FireBaseHelper.StartSyncingfullData(Synced_JSONData,FireBaseHelper.FirebaseJsonData)
        except Exception as ex:
            print (ex)

        return Synced_JSONData
    #N U
    def SyncwithLocalbaseData(URLToSync, SwimerURLToSync=""):
        try:
            #init Timer
            StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart
            # if internet fails load the last local file only
            if (FireBaseHelper.DownloadFirebaseToLocal(URLToSync+FireBaseHelper.strjson,FireBaseHelper.FirebaseJSONFilePath)==False):
                FireBaseHelper.FirebaseJsonData=FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)

            # if internet fails load the last local file only
            if (FireBaseHelper.LoadSwimmerTableToFile(SwimerURLToSync+ FireBaseHelper.strjson,FireBaseHelper.FirebaseSwimmerTable)==False):
                FireBaseHelper.SwimmerTable= FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseSwimmerTable)

            #JsonDataFromFirebase= FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            #JsonSwimmerDataFromFirebase = FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            PreviousLocalResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            Synced_JSONData= FireBaseHelper.SyncFileWithpreviousResults(FireBaseHelper.FirebaseJsonData,PreviousLocalResultData)

            #For Syncing SwimmerData with Local SwimmerData
            #PreviousLocalSwimmerData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteSwimmerTablePath)
            #Synced_SwimmerData= FireBaseHelper.SyncFileWithpreviousSwimmerData(FireBaseHelper.FirebaseSwimmerTable,PreviousLocalSwimmerData)

            # Kept here for testing to be moved to Heat completionTake Synced Data , Compare with FB Swimmer List, if any changes needed update to FB
            FireBaseHelper.SyncFirebasefullSwDatawithlatestResults(Synced_JSONData,FireBaseHelper.SwimmerTable)

            #For Syncing All Main Data to Firebase
            FireBaseHelper.StartSyncingfullData(Synced_JSONData,FireBaseHelper.FirebaseJsonData)
        except Exception as ex:
            print (ex)
        return Synced_JSONData

    @app.route('/InitFirebaseData', methods=['GET'])
    def InitFirebaseData():
        try:
            URLToSync = request.args.get('URLToSync')
            FireBaseHelper.EventBaseurl = URLToSync
            RestServicecls.NextSetHeatID= "WaitingToStart"
            StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart
            FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.EventBaseurl+FireBaseHelper.strjson,FireBaseHelper.FirebaseJSONFilePath)
            JsonData=FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            JsonDataFromFirebase= FireBaseHelper.GetJSONFromFile(FireBaseHelper.FirebaseJSONFilePath)
            PreviousResultData= FireBaseHelper.FormatHeatresultFiletoProperJSONandRead(FireBaseHelper.WriteHeatResultsPath)
            JsonData= FireBaseHelper.SyncFileWithpreviousResults(JsonData,PreviousResultData)
            FireBaseHelper.StartSyncingfullData(JsonData,JsonDataFromFirebase)
            FireBaseHelper.LoadSwimmerTable()
            response =  jsonify({'HeatDetails': "OK"})
        except Exception as ex:
            print (ex)
            response =  jsonify({'HeatDetails': "NOK"})

        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")

        return response

    def GetNextHeatID(data):
        #data= JsonHelper.GetJSONFromFile(JSONFilePath)
        # VCR TO BE DONE Check if any Request from Reffree Console
        if (RestServicecls.AutoFindHeat== 1):
            HeatID, EventID= JsonHelper.GetNextHeatIDFromFile(data)
        # elif(RestServicecls.NextSetHeatID=="WaitingToStart"):
        #     HeatID = RestServicecls.NextSetHeatID
        #     EventID=""
        else:
            HeatID = RestServicecls.NextSetHeatID
            # RestServicecls.NextSetHeatID=""
            EventID=""
        RestServicecls.NextSetHeatID= HeatID
        RestServicecls.TimerState="State"
        RestServicecls.TimerStateMessage= 'NewHeat'
        return HeatID, EventID

    @app.route('/')
    def index():        
        return render_template('LiveDisplayPage.html')        
        # return render_template('LiveDisplayPage.html')

    @app.route('/TimeKeeper')
    def TimeKeeper():
        # Should have call for
        return render_template('TimeKeeper.html')

    @app.route('/MeetEditor')
    def MeetEditor():
        try:
            return render_template('MeetReportGenerator.html')
            # return xx
        except Exception as ex:
            print (ex)       

        # Should have call for

    @app.route('/LiveControl')
    def LiveCtrl():
        # Should have call for
        return render_template('EejoTimerControl.html')
    @app.route('/Reports')
    def Reports():
        # Should have call for
        return render_template('MultiSelectTest.html')
# N U
    # GET requests will be blocked Not used
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
# N U
    # @app.route('/GetMeetHeaders', methods=['POST'])
    # def GetDisplayHeaders():
    #     data= JsonHelper.GetJSONFromFile(JSONFilePath)
    #     MeetDetail=JsonHelper.GetMeetHeader(data)
    #     response =  jsonify({'MeetDetail': MeetDetail})
    #     response.headers.add("Access-Control-Allow-Origin", "*")
    #     response.headers.add("Access-Control-Allow-Headers", "*")
    #     response.headers.add("Access-Control-Allow-Methods", "*")
    #     return response

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
# Good But To be Utilised.
    @app.route('/DownloadFBToLoaclFile', methods=["GET"])
    def DownloadFBToLoaclFile():
        try:
            FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.EventBaseurl+FireBaseHelper.strjson,FireBaseHelper.JSONFilePath)
            response =  jsonify({'HeatDetails': "Downloading Sucessfull at location " + FireBaseHelper.JSONFilePath})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
        except Exception as ex:
            print (ex)

        return response

    @app.route('/GetTimerState', methods=["GET"])
    def GetTimerState():
        try:
            response =  jsonify({'TimerState':str(RestServicecls.TimerState),'Message':str(RestServicecls.TimerStateMessage)})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")

        except Exception as ex:
            print (ex)

        return response

    @app.route('/SetLiveHeatCommands', methods=["GET"])
    def SetLiveHeatCommands():
        try:
            commandname = request.args.get('CmdName')
            commandReturnData=""
            if (commandname== 'CurrentBitAlocation'):
                commandReturnData= {'SIDE_A_SwBits':StopTimerServicecls.SIDE_A_SwBits,
                'SIDE_B_SwBits':StopTimerServicecls.SIDE_B_SwBits}


            elif (commandname== 'SetBitAlocation'):
                ReqSideAB= request.args.get('SIDE_A_SwBits').split(",")
                StopTimerServicecls.SIDE_A_SwBits = [int(item) for item in ReqSideAB]
                ReqSideAB= request.args.get('SIDE_B_SwBits').split(",")
                StopTimerServicecls.SIDE_B_SwBits=  [int(item) for item in ReqSideAB]
                PrimerySide= request.args.get('PrimerySide')
                if (PrimerySide == "PrimeryB"):
                    StopTimerServicecls.MODSwitchBits= StopTimerServicecls.SIDE_B_SwBits
                else:
                    StopTimerServicecls.MODSwitchBits= StopTimerServicecls.SIDE_A_SwBits

            elif (commandname== 'StopWatchSwStatus'):
                # RestServicecls.Synced_JSONData
                commandReturnData= {'StopWatchSwStatus':ModbusLibcls.StopWatchSwStatus}
                                
            elif (commandname== 'showQRDisplay'):
                HideCmd = request.args.get('HideCmd')
                if (HideCmd=='1'):
                    RestServicecls.TimerState="State"
                    RestServicecls.TimerStateMessage= "HideQR"
                else:
                    RestServicecls.TimerState="State"
                    RestServicecls.TimerStateMessage= "ShowQR"
                commandReturnData = {'cmd':HideCmd}

            elif (commandname== 'GetMeetInfo'): 
                # RestServicecls.Synced_JSONData
                commandReturnData= {'MeetName':RestServicecls.Synced_JSONData ['MeetName'],
                'Boards':RestServicecls.Synced_JSONData ['Boards'],
                'MeetAddress':RestServicecls.Synced_JSONData ['MeetAddress'],
                'MeetDate':RestServicecls.Synced_JSONData ['MeetDate']}

            elif (commandname== 'GetHeatInfo'):                     
                commandReturnData= {'HeatName':RestServicecls.NextSetHeatID}

            elif (commandname== 'GetSwNames'): 
                HeatData =  StopTimerServicecls.heatDataDisplay
                SwNames=[]
                for board in HeatData.SwimerBoardDetails:
                    SwNames.append(board.swimmername)
                commandReturnData = {'SwNames':SwNames}
            elif (commandname== 'GetBoardStatusAndTime'): 
                HeatData =  StopTimerServicecls.heatDataDisplay
                BoardStatusAndTime=[]
                for board in HeatData.SwimerBoardDetails:
                    BoardStatusAndTime.append({'BoardID':board.boardId,'Time':board.timerValue,'Status':board.swimerStatus,'LockStatus':board.LockTime})
                commandReturnData = {'BoardStatusAndTime':BoardStatusAndTime}

            elif (commandname== 'GetHeatStatus'): 
                commandReturnData = {'BoardTimeings':['Tim1', 'Sw2']}

            elif (commandname== 'GetRestIP'): 
                commandReturnData= RestServicecls.GetRestIP()

            elif (commandname== 'GetRunningHeatData'): 
                commandReturnData= RestServicecls.Synced_JSONData
            
            elif (commandname== 'SetRunningHeatData'):                      
                HeatData = request.args.get('HeatData')
                RestServicecls.InitStatus = 1
                FireBaseHelper.SetJSONToFile(HeatData,FireBaseHelper.FirebaseJSONFilePath)
                RestServicecls.Synced_JSONData= json.load(HeatData)
                RestServicecls.InitStatus = 0
                StopTimerServicecls.StartRestcommand =3
                StopTimerServicecls.SetHeatStatus(TimerStatus.WaitingToStart)
                StopTimerServicecls.ResetTimer()
                

            elif (commandname== 'SetFBPathtoSync'): 
                URLToSync = request.args.get('URLToSync')
                FireBaseHelper.EventBaseurl = URLToSync

            elif (commandname== 'SyncToSwimmerTable'): 
                    # To be Implemented
                URLToSync = request.args.get('URLToSync')
                FireBaseHelper.EventBaseurl = URLToSync

            elif (commandname== 'GetAllHeatIDsFromFile'): 
                commandReturnData = JsonHelper.GetAllHeatIDsFromFile(RestServicecls.Synced_JSONData)
            elif (commandname== 'InitTimerFromFirebase'): 
                RestServicecls.InitStatus = 1
                URLToSync = request.args.get('URLToSync')
                # SwimerURLToSync=  request.args.get('SwimerURLToSync')
                OverWriteOption=  request.args.get('OverWriteOption')
                FireBaseHelper.EventBaseurl = URLToSync
                # FireBaseHelper.SwimmerURL=SwimerURLToSync
                RestServicecls.LoaDataFromFirebaseData(URLToSync,int(OverWriteOption))

            elif (commandname== 'InitTimerFromLocalFile'): 
                RestServicecls.InitStatus = 1
                HeatFileName = request.args.get('HeatFileName')
                OverWriteOption=  request.args.get('OverWriteOption')                    
                RestServicecls.LoadDataFromLocalFile(HeatFileName,int(OverWriteOption))

            elif (commandname== 'InitHeatFromLocalDisk'):
                RestServicecls.InitStatus = 1
                HeatFileDiskpath = request.args.get('HeatFileDiskpath')
                OverWriteOption=  request.args.get('OverWriteOption')                    
                RestServicecls.LoadDataFromLocalFile("",int(OverWriteOption),HeatFileDiskpath)

            elif (commandname== 'SaveHeatFileToLocalFile'): 
                RestServicecls.InitStatus = 2
                HeatData = request.args.get('HeatData')
                FileNametoSave = request.args.get('FileNametoSave')
                RestServicecls.SaveHeatFileToLocalFile(HeatData,FileNametoSave)

            elif (commandname== 'ReadHeatFromLocalFile'): 
                HeatFileName=  request.args.get('HeatFileName')
                commandReturnData= RestServicecls.ReadHeatFromLocalFile(HeatFileName)

          

            #  elif (commandname== 'SetBitAlocation'): 'LoadHeatFromLocalFile':
            #     HeatFileName=  request.args.get('HeatFileName')
            #     commandReturnData= RestServicecls.LoadHeatFromLocalFile(HeatFileName)

            elif (commandname== 'SetBitAlocaAutoFindHeattion'): 
                RestServicecls.AutoFindHeat =int( request.args.get('AutoCmd'))
                StopTimerServicecls.StartRestcommand =3
                StopTimerServicecls.SetHeatStatus(TimerStatus.WaitingToStart)
                StopTimerServicecls.ResetTimer()

            elif (commandname== 'SetNextHeat'): 
                RestServicecls.AutoFindHeat=0
                HeatName = request.args.get('HeatName')
                #StopTimerServicecls.StartRestcommand =3
                RestServicecls.NextSetHeatID= HeatName
                StopTimerServicecls.SetHeatStatus(TimerStatus.WaitingToStart)
                StopTimerServicecls.ResetTimer()

            elif (commandname== 'HeatCommand'):  # 1-Start, 2-Pause,3-Stop,4-Repeat
                HeatcmdValue = request.args.get('HeatCmdValue')
                StopTimerServicecls.ResetTimer()
                StopTimerServicecls.StartRestcommand =int(HeatcmdValue)
                # if (StopTimerServicecls.StartRestcommand==4):
                #     StopTimerServicecls.SetHeatStatus(TimerStatus.Completed)

                print(str(commandname) + str (HeatcmdValue))

            elif (commandname== 'SwimmerNameDispCmd'):  # SwBoardID=""&SwNameValue=""
                SwBoardID = int (request.args.get('SwBoardID'))
                SwNameValue = request.args.get('SwNameValue')
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[SwBoardID].swimmername=SwNameValue
                print(commandname +  SwBoardID + SwNameValue)
                #TBD

            elif (commandname== 'SwimmerTimeDispCmd'):  # SwBoardID=""&SwTimeValue=""
                SwBoardID = int (request.args.get('SwBoardID'))
                SwTimeValue = int(request.args.get('SwTimeValue'))
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[SwBoardID].timerValue=SwTimeValue
                print(commandname +  SwBoardID + SwTimeValue)
                #TBD

            elif (commandname== 'SwimmerStatusCmd'):   # SwBoardID=""&SwStatusCmdValue="" 0-NA, 1-AB,2-DQ,3-DNC
                SwBoardID =int (request.args.get('SwBoardID'))
                SwStatusCmdValue = int(request.args.get('SwStatusCmdValue'))
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[SwBoardID].swimerStatus=SwStatusCmdValue
                print(commandname +  SwBoardID + SwStatusCmdValue)
                #TBD

            elif (commandname== 'BoardTimerCmd'):  # SwBoardID=""&BoardTimerCmdValue="" #  1-Pause,2-Continue,3-Disable,4-Bypass
                SwBoardID = request.args.get('SwBoardID')
                BoardTimerCmdValue = request.args.get('BoardTimerCmdValue')
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[int(SwBoardID)].RestBoardTimerCmd=int(BoardTimerCmdValue)
                print(commandname + SwBoardID + BoardTimerCmdValue)
                #TBD

            #  elif (commandname== 'SetBitAlocation'): 1:

            elif (commandname== 'default'):
                print("at default")


            response =  jsonify({'commandname':commandname,'commandReturnData': commandReturnData})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
        except Exception as ex:
            print (ex)
        return response
# N U
# GET requests will be blocked NOT USED
    @app.route('/SetLiveHeatDetails', methods=['POST'])
    def SetLiveHeatDetails():
        request_data = request.get_json()
        return str(HeatDataDisplay)

    @app.route('/LiveTimer', methods=['GET'])
    def LiveTimer():
        HeatData =  StopTimerServicecls.heatDataDisplay
        sjson=[]
        for board in HeatData.SwimerBoardDetails:
            sjson.append(json.dumps(board.__dict__) )
        response =  jsonify({'Boards': sjson})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response