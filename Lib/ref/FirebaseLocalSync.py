from urllib.request import urlopen
import requests
from time import sleep
import json  
class Changeinfo:

    # Possible Improvements []
    # [VCR 01-02-25] Main Thread to send canges insted of this class detecting changes by scanning Local File :PENDING

#event,heat,board
    def __init__(self, event,heat,board,swimTimings,writeStatus):
        self.eventID = event
        self.heatID = heat
        self.boardID = board
        self.SwimTimings = swimTimings
        self.WriteStatus=writeStatus

class FireBaseHelper:
    MeetNumber=0
    #JsonFilepath ="/home/pks/Desktop/Pi-py Web Server/FirebaseJSONData.json"
    FirebaseFilepath ="C:\\users\\vchikkay\\OneDrive - Alstom\\Data\\projects\\Vinnovation\\TinyTechniques\\EEjo\\Pi-py Web Server\\Lib\\FirebaseHelper.json"
    LocalFilepath ="C:\\users\\vchikkay\\OneDrive - Alstom\\Data\\projects\\Vinnovation\\TinyTechniques\\EEjo\\Pi-py Web Server\\Lib\\FirebaseHelperLocal.json"
    Baseurl = "https://eejo-managerdb-default-rtdb.firebaseio.com/Meets/"+ str(MeetNumber)
    ChangenidentifiedforFirebase=[]
    ChangenidentifiedforLocal=[]

    

    def internet_on_async():
        try:
            response=urlopen('http://74.125.228.100',timeout=20)
            return True
        except urllib2.URLError as err: pass
        return False
    def DownloadFirebaseToLocal(url,Filepath):
        if (FireBaseHelper.internet_on_async):
            response = urlopen(url+".json")
            data_json = json.loads(response.read())
            # print(data_json)
            with open(Filepath, 'w') as f:
                json.dump(data_json, f)
        return

    def GetJSONFromFile(ReadJsonPath,MeetNumber):
        with open(ReadJsonPath,"r") as f:
            data= json.load(f)            
        return	data

    def generate_heat_update_list(LocalData, FirebaseData):
        if (LocalData!= None  and FirebaseData!=None ):            
            
            for event in range(0,len(LocalData["EventDetails"])):
                for heat in range(0,len (LocalData["EventDetails"][event]["HeatList"])):
                    for board in range(0,len (LocalData["EventDetails"][event]["HeatList"][heat]["BoardList"])): 
                        if (LocalData["EventDetails"][event]["HeatList"][heat]["BoardList"][board]["SwimTimings"] != FirebaseData["EventDetails"][event]["HeatList"][heat]["BoardList"][board]["SwimTimings"]):
                            FireBaseHelper.ChangenidentifiedforFirebase.append(Changeinfo(event,heat,board,LocalData["EventDetails"][event]["HeatList"][heat]["BoardList"][board]["SwimTimings"],0))
                            
                        if (LocalData["EventDetails"][event]["HeatList"][heat]["BoardList"][board]["SwimerID"] != FirebaseData["EventDetails"][event]["HeatList"][heat]["BoardList"][board]["SwimerID"],0):
                            FireBaseHelper.ChangenidentifiedforLocal.append(Changeinfo(event,heat,board,1,0))
                            # print(LocalData[event]["HeatList"][heat]["BoardList"][board])
            return FireBaseHelper.ChangenidentifiedforFirebase, FireBaseHelper.ChangenidentifiedforLocal
            
        return

if (FireBaseHelper.internet_on_async):
    FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.Baseurl,FireBaseHelper.FirebaseFilepath)

    FirebaseData= FireBaseHelper.get_json(FireBaseHelper.FirebaseFilepath,FireBaseHelper.MeetNumber)

    LocalData=  FireBaseHelper.get_json(FireBaseHelper.LocalFilepath,FireBaseHelper.MeetNumber)

    while True:
        sleep(0.1)
        LocalData=  FireBaseHelper.get_json(FireBaseHelper.LocalFilepath,FireBaseHelper.MeetNumber)
        #LocalData=  FireBaseHelper.get_json(FireBaseHelper.LocalFilepath,FireBaseHelper.MeetNumber)
        FireBaseHelper.generate_heat_update_list(LocalData,FirebaseData)    
        #print("For Firebase")
        for changelog in range(0,len(FireBaseHelper.ChangenidentifiedforFirebase)):
            sync= FireBaseHelper.ChangenidentifiedforFirebase[changelog]
            if (FireBaseHelper.ChangenidentifiedforFirebase[changelog].WriteStatus==0):
                url= FireBaseHelper.Baseurl+ '/' + str(sync.eventID) +"/HeatList/"+ str(sync.heatID)+"/BoardList/"+ str(sync.boardID)+".json"
                response = urlopen(FireBaseHelper.Baseurl+ '/' + str(sync.eventID) +"/HeatList/"+ str(sync.heatID)+"/BoardList/"+ str(sync.boardID)+"/SwimTimings.json")  
                if (sync.SwimTimings!= json.loads(response.read())):
                    str1 = '{"SwimTimings":'+str(sync.SwimTimings)+'}' 
                    r = requests.patch(url, data = str1)
                    print (url)
                   # print (str(sync.eventID)  + str(sync.heatID) + str(sync.boardID))
                    print(r.content)
                else:
                    ChangenidentifiedforFirebase[changelog].WriteStatus=1
    
    # print("For Local")
    # for sync in ChangenidentifiedforLocal:
    #     print (str(sync.eventID)  + str(sync.heatID) + str(sync.boardID))
