from Lib.StopwatchLib import StopTimerServicecls
from Lib.RestServicesLib import RestServicecls
from Lib.SwimDataHolder import TimerStatus,swimstatus,SwimerBoardDetail
from Lib.JsonLib import JsonHelper
from Lib.LogerService import Logger
import threading


# while True:
#     Logger.app_log.info("data")

RestServicecls.SetStartTimercmd=1
SwimerBoardDetails= []
StopTimerServiceclsobj=StopTimerServicecls()
StopTimerServiceclsobj.HeatStatus= TimerStatus.WaitingToStart
JSONFilePath= "/home/pks/Desktop/Pi-py Web Server/Data/MeetDetails.json"
WriteJsonPath= "/home/pks/Desktop/Pi-py Web Server/Data/MeetDetails.json"

# StopTimerServiceclsobj.ResetTimer()
# StopTimerServiceclsobj.PrepareHeat(2,SwimerBoardDetails)
#Logger.app_log.info("waiting to Next Heat Start")
#Logger.app_log.info("waiting to Next Heat Start")

threading.Thread(target=lambda: RestServicecls.app.run(host=RestServicecls.host_name, port=RestServicecls.port, debug=False, use_reloader=False)).start()
while True:
    # From Rest Server Read all heats in loop  or receive heat from other terminal.
    HeatStatus = StopTimerServiceclsobj.getHeatStatus()

    if (HeatStatus== TimerStatus.WaitingToStart ):
        Logger.app_log.info("waiting to Next Heat Start")
#         Logger.app_log.info("waiting to Next Heat Start")
        HeatID=RestServicecls.GetNextHeatID()
        if (HeatID!=0):
            data= JsonHelper.GetJSONFromFile(JSONFilePath)
            Logger.app_log.info("Loaded Heat "+ str(HeatID))
            heatDataDisplay = JsonHelper.GetHeatDataDisplay(HeatID,data)

            StopTimerServiceclsobj.ResetTimer()
            StopTimerServiceclsobj.PrepareHeat(3,SwimerBoardDetails)
            StopTimerServiceclsobj.SetHeatStatus(TimerStatus.loadedToStart)
        else:
            print ("No Heats Found")

    elif(HeatStatus== TimerStatus.Completed):
        print (HeatID)
        data= JsonHelper.GetJSONFromFile(JSONFilePath)
        JsonHelper.setHeatResults(HeatID, StopTimerServiceclsobj.GetHeatStartTime(),StopTimerServiceclsobj.GetHeatEndTime(),data, StopTimerServiceclsobj.GetSwimboardDetails())
        JsonHelper.SetJSONToFile (data,WriteJsonPath)
        StopTimerServiceclsobj.SetHeatStatus(TimerStatus.WaitingToStart)


        # Update Resutls to File
    elif ( HeatStatus== TimerStatus.loadedToStart or HeatStatus== TimerStatus.InProgress):
        StopTimerServiceclsobj.RunTimer()




    #print (HeatStatus)
#     if (HeatStatus != TimerStatus.Completed):
        #Logger.app_log.info("Timer Running")
#         StopTimerServiceclsobj.RunTimer()
#     else:
#         print ("waiting to Next Heat Start")
#         Logger.app_log.info("waiting to Next Heat Start")
        #Logger.app_log.info("waiting to Next Heat Start")
#         HeatID=RestServicecls.GetNextHeatID()
#         if (HeatID!=""):
#             JSONFilePath= "/home/pks/Desktop/Pi-py Web Server/Data/MeetDetails.json"
#             data= JsonHelper.GetJSONFromFile(JSONFilePath)
#             heatDataDisplay = JsonHelper.GetHeatDataDisplay(HeatID,data)
#             StopTimerServiceclsobj=StopTimerServicecls()
         #   StopTimerServicecls.HeatStatus= TimerStatus.InProgress
#             StopTimerServiceclsobj.ResetTimer()
#             StopTimerServiceclsobj.PrepareHeat(3,SwimerBoardDetails)


            # StopTimerServiceclsobj.PrepareHeat(len(heatDataDisplay.SwimerBoardDetails),heatDataDisplay.SwimerBoardDetails)
#             StopTimerServiceclsobj.ResetTimer()
#             StopTimerServiceclsobj.HeatStatus=TimerStatus.WaitingToStart

print("Hello")