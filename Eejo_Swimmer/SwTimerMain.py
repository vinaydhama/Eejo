from Lib.StopwatchLib import StopTimerServicecls
from Lib.RestServicesLib import RestServicecls
from Lib.SwimDataHolder import TimerStatus,SwimerBoardDetail
from Lib.JsonLib import JsonHelper
from Lib.LogerService import Logger
from Lib.FirebaseHelper import FireBaseHelper
import threading
#import os


RestServicecls.SetStartTimercmd=1
SwimerBoardDetails= []

StopTimerServicecls.HeatStatus= TimerStatus.WaitingToStart
JSONFilePath= "/home/pks/Desktop/Eejo_Swimmer/Data/FirebaseJSONData.json"
WriteJsonPath= "/home/pks/Desktop/Eejo_Swimmer/Data/FirebaseJSONData.json"
HeatID=""
EventID=""
#FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.url,JSONFilePath)

threading.Thread(target=lambda: RestServicecls.app.run(host=RestServicecls.host_name, port=RestServicecls.port, debug=False, use_reloader=False)).start()

# Launch Browser
# cmd = "/usr/bin/chromium-browser  --start-fullscreen http://localhost:5002/"
# os.system(cmd)

# Downloading data from Firebase
# FireBaseHelper.DownloadFirebaseToLocal(FireBaseHelper.url,FireBaseHelper.JsonFilepath)
# FirebaseJsondata= FireBaseHelper.GetJSONFromFile(FireBaseHelper.JsonFilepath)
# print(data)

# print(url)
while True:
    # From Rest Server Read all heats in loop  or receive heat from other terminal.
    HeatStatus = StopTimerServicecls.getHeatStatus()
    print (HeatStatus)

    if (HeatStatus== TimerStatus.WaitingToStart ):
        Logger.app_log.info("waiting to Next Heat Start")
        HeatID,EventID=RestServicecls.GetNextHeatID(JSONFilePath)
        if (HeatID!=0):
            data= JsonHelper.GetJSONFromFile(JSONFilePath)
            Logger.app_log.info("Loaded Heat "+ str(HeatID))
            heatDataDisplay = JsonHelper.GetHeatDataDisplay(HeatID,EventID,data)

            StopTimerServicecls.ResetTimer()
            StopTimerServicecls.PrepareHeat(heatDataDisplay)
            StopTimerServicecls.SetHeatStatus(TimerStatus.loadedToStart)
        else:
            print ("no heats found")

    elif(HeatStatus== TimerStatus.Completed):
        data= JsonHelper.GetJSONFromFile(JSONFilePath)
        #JsonHelper.setHeatResults(HeatID, StopTimerServicecls.heatDataDisplay,data)
        Updateddata, HeatID, eventID= FireBaseHelper.setHeatResultstoLocalJSONDB(HeatID,EventID,heatDataDisplay,data)
        #FireBaseHelper.setHeatResultstoFirebase( HeatID, eventID,Updateddata)
        #url = FireBaseHelper.setHeatResultstoFirebase(HeatID,data)
        JsonHelper.SetJSONToFile (data,WriteJsonPath)
        StopTimerServicecls.SetHeatStatus(TimerStatus.WaitingToStart)


        # Update Resutls to File
    elif ( HeatStatus== TimerStatus.loadedToStart or HeatStatus== TimerStatus.InProgress or HeatStatus== TimerStatus.WaitBeforeLoad or HeatStatus== TimerStatus.ResetbeforeStart
    or HeatStatus== TimerStatus.Stoped):
        StopTimerServicecls.RunTimer()