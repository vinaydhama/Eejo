from urllib.request import urlopen
import requests
import json
from Lib.LogerService import Logger
from Lib.SwimDataHolder import Changeinfo
from pathlib import Path
import os
import shutil


class FireBaseHelper:
    SwimmerTable=""
    MeetID="meetID"
    FirebaseJsonData=""
    MeetName=1
    # parent directory
    parentpath = os.path.dirname(Path(__file__).parent.absolute())
    FirebaseJSONFilePath = os.path.join(parentpath,"Data","FirebaseJSONData_Local.json")
    FirebaseSwimmerTable = os.path.join(parentpath,"Data","FirebaseSwimmerTable.json")
    WriteHeatResultsPath= os.path.join(parentpath,"Data","HeatExecutionResult.json")
    WriteSwimmerTablePath= os.path.join(parentpath,"Data","SwimmerTableResults.json")


    # JSONFilePath="C:\\Users\\vchikkay\\OneDrive - Alstom\\Data\\projects\\Vinnovation\\TinyTechniques\\EEjo\\eejo_Swimmer\\Eejo\\Eejo_Swimmer\\Lib\\FirebaseJSONData_Local.json"
    strjson= ".json"
    Eventurl= "https://eejo-managerdb-default-rtdb.firebaseio.com/Meets/"
    EventBaseurl = Eventurl + str(MeetName)
    SwimmerURL= "https://eejo-managerdb-default-rtdb.firebaseio.com/Swimmers"

    ChangenidentifiedforFirebase=[]


    def CopyHeatFile(FileSourcePath, FileDestPath):
        try:
            if os.path.exists(FileSourcePath):
                if os.path.exists(FileDestPath):
                    os.remove(file_path)
                shutil.copy(FileSourcePath, FileDestPath)
                return True
            else:
                print("The file "+ file_path + " Not exists")
                return True
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return False

    def DeleteHeatFile(file_path):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            else:
                # print("The file '{file_path}' already exists")
                return True
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return False

    
    def CreateifFiledontExists(file_path):
        try:
            if not os.path.exists(file_path):
                with open(file_path, 'w+') as file:
                    file.write("")
                return True
            else:
                # print("The file '{file_path}' already exists")
                return True
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return False

    def internet_on():
        try:
            requests.get('http://clients3.google.com/generate_204',timeout=5)
            #response=urlopen('https://www.google.com/',timeout=5)
            return True

            #return True
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return False
# This Function can be used to download Heat From FB to Local File DUPLICATE OF DownloadFirebaseToLocal

    def DownloadFirebaseToLocal (url,Filepath):
        if (FireBaseHelper.internet_on() and FireBaseHelper.CreateifFiledontExists(Filepath)):
            # FireBaseHelper.SwimmerTable= json.loads(response.read())
            try:
                response = urlopen(url)
                FireBaseHelper.SwimmerTable = json.loads(response.read())                
                with open(Filepath, 'w+') as f:
                    json.dump(FireBaseHelper.SwimmerTable, f)
            except Exception as ex:
                Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
            return FireBaseHelper.SwimmerTable
        return False
    #VCR Not used
    def generateTimeUpdateListsforFirebase(LocalData, FirebaseData):
        if (LocalData!= None  and FirebaseData!=None ):
            for event in range(0,len(Localdata)):
                for heat in range(0,len (Localdata[event]["HeatList"])):
                    for board in range(0,len (Localdata[event]["HeatList"][heat]["BoardList"])):
                        if (Localdata[event]["HeatList"][heat]["BoardList"][board]["SwimTimings"] != Firebasedata[event]["HeatList"][heat]["BoardList"][board]["SwimTimings"]):
                            FireBaseHelper.ChangenidentifiedforFirebase.append(Changeinfo(event,heat,board,Localdata[event]["HeatList"][heat]["BoardList"][board]["SwimTimings"],0))

                        if (Localdata[event]["HeatList"][heat]["BoardList"][board]["SwimerID"] != Firebasedata[event]["HeatList"][heat]["BoardList"][board]["SwimerID"],0):
                            FireBaseHelper.ChangenidentifiedforLocal.append(Changeinfo(event,heat,board,1,0))
            return FireBaseHelper.ChangenidentifiedforFirebase, FireBaseHelper.ChangenidentifiedforLocal

        return

    def generateHeatUpdateListsforFirebase(LocalData, FirebaseData):
        if (LocalData!= None  and FirebaseData!=None ):
            for event in range(0,len(LocalData)):
                for heat in range(0,len (LocalData[event]["HeatList"])):
                        if (LocalData[event]["HeatList"][heat] ["HeatStartTime"]!= 0):
                            if (LocalData [event]["HeatList"][heat] ["HeatID"]== FirebaseData[event] ["HeatList"][heat]["HeatID"]):
                                if (LocalData[event]["HeatList"][heat] !=  FirebaseData[event]["HeatList"][heat]):
                                    FireBaseHelper.ChangenidentifiedforFirebase.append(Changeinfo(event,heat,LocalData[event]["HeatList"][heat],0,0) )

        return FireBaseHelper.ChangenidentifiedforFirebase

#NU
    def AppendHeatResult(AppendJsonPath,dataToUpdate):
        try:
            with open(AppendJsonPath, "a+") as json_file:
                json_file.write("{}\n".format(json.dumps(dataToUpdate)))
            return
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
#NU
    def AppendSwimmerResults(AppendJsonPath,dataToUpdate):
        try:
            with open(AppendJsonPath, "a+") as json_file:
                json_file.write("{}\n".format(json.dumps(dataToUpdate)))
            return
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)

    #VCR Not used due to new design
    #NU
    def StartSyncingSingleHeat(WriteHeatResultsPath, Changeinfoobj):
        if (FireBaseHelper.internet_on()):
            if (Changeinfoobj.WriteStatus==0):
                url= FireBaseHelper.Baseurl+ '/' + str(Changeinfoobj.eventID) +"/HeatList/"+ str(Changeinfoobj.heatID)+"/BoardList/"+ str(Changeinfoobj.boardID)+".json"
                response = urlopen(FireBaseHelper.Baseurl+ '/' + str(Changeinfoobj.eventID) +"/HeatList/"+ str(Changeinfoobj.heatID)+"/BoardList/"+ str(Changeinfoobj.boardID)+"/SwimTimings.json")
                if (Changeinfoobj.SwimTimings!= json.loads(response.read())):
                    str1 = '{"SwimTimings":'+str(Changeinfoobj.SwimTimings)+'}'
                    r = requests.patch(url, data = str1)
                    print (url)
                    print(r.content)
                else:
                    Changeinfoobj.WriteStatus=1
                    FireBaseHelper.ChangenidentifiedforFirebase.append(Changeinfoobj)
        return

    def StartSyncingfullData(LocalData, FirebaseData):
        if (FireBaseHelper.internet_on()):           
                FireBaseHelper.ChangenidentifiedforFirebase=[]
                FireBaseHelper.generateHeatUpdateListsforFirebase(LocalData,FirebaseData)
                for changelog in range(0,len(FireBaseHelper.ChangenidentifiedforFirebase)):
                    sync= FireBaseHelper.ChangenidentifiedforFirebase[changelog]
                    if (FireBaseHelper.ChangenidentifiedforFirebase[changelog].WriteStatus==0):
                        url= FireBaseHelper.EventBaseurl+ '/' + "EventDetails"+'/' + str(sync.eventID) +"/HeatList/"+ str(sync.heatID)+".json"                        
                        HeatJSON= json.dumps(sync.data)
                        r = requests.patch(url, data = HeatJSON)
                        print (url)
                        print(r.content)
                  

    def DownloadFirebaseToLocal(url,Filepath):
        if (FireBaseHelper.internet_on() and FireBaseHelper.CreateifFiledontExists(Filepath)):
            try:
                response = urlopen(url)
                FireBaseHelper.FirebaseJsonData = json.loads(response.read())
                with open(Filepath, 'w+') as f:
                    json.dump(FireBaseHelper.FirebaseJsonData, f)

            except Exception as ex:
                Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
            return FireBaseHelper.FirebaseJsonData
        return

    def PrepareHeatResultstoLocalJSONDB(HeatIDToUpdate,heatDataDisplay,data):
        try:
            for eventID in range(0,len(data['EventDetails'])):
                event= data['EventDetails'][eventID]
                # if (event["eventID"]==EventIDToUpdate):
                for heat in range(0,len (event["HeatList"])):
                    if (HeatIDToUpdate==event["HeatList"][heat]["HeatID"]):
                        print("HeatID" + event["HeatList"][heat]["HeatID"])

                        event["HeatList"][heat]["HeatStartTime"]= heatDataDisplay.HeatStartTime
                        event["HeatList"][heat]["HeatEndTime"]= heatDataDisplay.HeatEndTime
                        print (event["HeatList"][heat]["HeatStartTime"])
                        print(event["HeatList"][heat]["HeatEndTime"])

                        for Board in range(0,len (event["HeatList"][heat]["BoardList"])):
                            event["HeatList"][heat]["BoardList"][Board]["SwimTimings"]=heatDataDisplay.SwimerBoardDetails[Board].timerValue
                            event["HeatList"][heat]["BoardList"][Board]["SwimStatus"]=heatDataDisplay.SwimerBoardDetails[Board].swimerStatus
                            print (event["HeatList"][heat]["BoardList"][Board]["SwimTimings"])
                        return data,event["HeatList"] [heat],heat, eventID
            return data,-1,-1,-1

        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return
        # this function is to add JSON Formaters for text file.
    def FormatHeatresultFiletoProperJSONandRead(ReadJsonPath):
        try:
            # Read in the file
            if (FireBaseHelper.CreateifFiledontExists(ReadJsonPath)):
                with open(ReadJsonPath, 'r') as file:
                    filedata = file.read()
                # Replace the target string
                filedata = filedata.replace('}\n{', '},{')
                filedata = filedata.replace('\n', '')
                filedata = filedata.replace('\'', '')
                filedata = "[" + filedata + "]"

                return json.loads(filedata)
                # # Write the file out again
                # with open(ReadJsonPath, 'w') as file:
                #     file.write(filedata)
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)

    def GetJSONFromFile(ReadJsonPath):
        try:
            with open(ReadJsonPath,"r") as f:
                data= json.load(f)
            return	data
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)

    def SetJSONToFile (data,WriteJsonPath):
        try:
            if (FireBaseHelper.CreateifFiledontExists(WriteJsonPath)):
                with open(WriteJsonPath,"w") as f:
                    json.dump(data,f)		
            return	
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
    
    def UpdateHeatResultToFirebaseSwimRecord(UpdatedHeat):
        try:
            EvetID= UpdatedHeat["HeatID"][:UpdatedHeat["HeatID"].rfind("_")]
            for board in (UpdatedHeat["BoardList"]):
                # changeobj.boardID = board["BoardID"]
                # changeobj.SwimTimings = board["SwimTimings"]
                FireBaseHelper.SetResultsToSwimmerRecord(board["SwimerName"],"MeetID",EvetID,UpdatedHeat["HeatEndTime"],board["SwimTimings"])
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)

# To be used for updating each heat
    def UpdateHeatResultToFirebase (UpdtatedHeatData,heatindex,eventIndex):
        try:
            if (FireBaseHelper.internet_on()):
                url= FireBaseHelper.EventBaseurl+ '/'+"EventDetails"+"/" + str(eventIndex) +"/HeatList/"+ str(heatindex)+".json"
                data1 = json.dumps(UpdtatedHeatData)
                r = requests.patch(url, data = data1)
            else:
                sleep(2)
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
    # To Update Firebase Swimmer Records
    def SetResultsToSwimmerRecord (SwName,MeetID,EvetID,HeatDateTime,timeings):
        if (FireBaseHelper.internet_on()):
            for SwNameIndex in range (0,len(FireBaseHelper.SwimmerTable)):
                if (FireBaseHelper.SwimmerTable[SwNameIndex]["Name"]== SwName):
                    urltoAdd= FireBaseHelper.SwimmerURL +"/" + str(SwNameIndex) + FireBaseHelper.strjson
                    FireBaseHelper.SwimmerTable[SwNameIndex]["MeetResults"].append({'EventID': EvetID, 'HeatDateTime':HeatDateTime, 'MeetID': FireBaseHelper.MeetID,'MyNotes': 'Notes', 'timeings': timeings})
                    data1 = json.dumps(FireBaseHelper.SwimmerTable[SwNameIndex])
                    r = requests.patch(urltoAdd, data = data1)
                    break
        return
    
    def SyncFirebasefullSwDatawithlatestResults(SyncedJsonData,SwimmerTable):
          if (SyncedJsonData!= None ):
            RecordtobeAdded= True
            for resultdata in SyncedJsonData:
                for event in SyncedJsonData:
                    for heat in event["HeatList"]:
                        for board in heat["BoardList"]:
                            for swimmer in SwimmerTable:
                                if swimmer["ID"]== board["SwimerID"]: 
                                    # Check if Record Exists
                                    for records in swimmer["MeetResults"]:
                                        if ((records["EventID"]!= event["eventID"])):
                                            if (records["MeetID"]!= FireBaseHelper.MeetID):
                                                if(records["HeatDateTime"]!=heat["HeatEndTime"]):
                                                    # Need To check is it OK To overwrite Timeings ??
                                                    if (records["timeings"]!=board["SwimTimings"]):
                                                        RecordtobeAdded= False 
                                                        break
                                                       
                                    if (RecordtobeAdded):
                                        FireBaseHelper.SetResultsToSwimmerRecord(swimmer["ID"],FireBaseHelper.MeetID,event["eventID"],board["SwimTimings"],heat["HeatEndTime"])
            return True

    def SyncFileWithpreviousResults(JsonDataFromFirebase,PreviousResultData):
          if (PreviousResultData!= None  and JsonDataFromFirebase!=None ):
            for PreviousresultHeat in PreviousResultData:
                for event in range(0,len(JsonDataFromFirebase['EventDetails'])):
                    for heat in range(0,len (JsonDataFromFirebase['EventDetails'][event]["HeatList"])):
                        if (PreviousresultHeat["HeatID"]== JsonDataFromFirebase['EventDetails'][event]["HeatList"][heat]["HeatID"]):
                            if (PreviousresultHeat != JsonDataFromFirebase['EventDetails'][event]["HeatList"][heat]):
                                JsonDataFromFirebase['EventDetails'][event]["HeatList"][heat] = PreviousresultHeat
                                print(str(PreviousresultHeat["HeatID"]))


                            # for board in range(0,len (JsonDataFromFirebase[event]["HeatList"][heat]["BoardList"])):
                            #     IF
                            #     if (JsonDataFromFirebase[event]["HeatList"][heat]["BoardList"][board]["SwimTimings"] != Firebasedata[event]["HeatList"][heat]["BoardList"][board]["SwimTimings"]):
                            #         FireBaseHelper.ChangenidentifiedforFirebase.append(Changeinfo(event,heat,board,JsonDataFromFirebase[event]["HeatList"][heat]["BoardList"][board]["SwimTimings"],0))

                            #     if (JsonDataFromFirebase[event]["HeatList"][heat]["BoardList"][board]["SwimerID"] != Firebasedata[event]["HeatList"][heat]["BoardList"][board]["SwimerID"],0):
                            #         FireBaseHelper.ChangenidentifiedforLocal.append(Changeinfo(event,heat,board,1,0))
            return JsonDataFromFirebase