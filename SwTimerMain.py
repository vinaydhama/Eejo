from Lib.StopwatchLib import StopTimerServicecls    
from Lib.WebServerLib import WebServerCls
from Lib.RestServicesLib import RestServicecls
from Lib.JsonLib import JsonHelper
from Lib.SwimDataHolder import TimerStatus,SwimerBoardDetail
from Lib.LogerService import Logger
from Lib.FirebaseHelper import FireBaseHelper
from Lib.ModbusLib import ModbusLibcls
import serial
import threading
from pathlib import Path
from Lib.UtilityFunctions import UtilityFunctions
import time
RestServicecls.SetStartTimercmd=1
ModbusConnectStatus=0
ModbusPortID=""
CompletedHeatList=[]
SwimerBoardDetails= []
ExecutedHeat=""
Updateddata=""
HeatID=""
EventID =""
threading.Thread(target=lambda: RestServicecls.app.run(host=RestServicecls.host_name, port=RestServicecls.port, debug=False, use_reloader=False)).start()

# Launch Browser
# cmd = "/usr/bin/chromium-browser  --start-fullscreen http://localhost:5002/"
# os.system(cmd)

# Enable For Modbus
# if platform.system() == "Windows":
#     ModbusPortID="COM6"
# else:
#     ModbusPortID="/dev/ttyUSB0"

# initModbusdevice(ModbusPortID,1,115200,8,serial.PARITY_NONE,1)

#ModbusLibcls.ConnecttoDevice()
RestServicecls.Synced_JSONData=RestServicecls.InitTimerStart()
WebServerCls.HTTPIP = RestServicecls.GetRestIP()
WebServerCls.init(WebServerCls.HTTPIP, WebServerCls.PORT)
threading.Thread(target=lambda: WebServerCls.httpd.serve_forever()).start()

# def schedule_reconnect():
#     ModbusLibcls.ConnecttoDevice()
#     UtilityFunctions.logScreenMsg("Reconnecting in 2 seconds...")
#     threading.Timer(2.0, connect_to_server).start()

# def schedule_DataRead():
#     # ModbusLibcls.GetStopWatchStatus()
#     # UtilityFunctions.logScreenMsg("Reconnecting in 2 seconds...")
#     threading.Timer(0.1, connect_to_server).start()


# def connect_to_server():
#     try:
#         ModbusLibcls.GetStopWatchStatus()
#         # ModbusConnectStatus=1
#         # UtilityFunctions.logScreenMsg("Connected to server!")
#         schedule_DataRead()
        
#         # You can now use `s` to send/receive data
#     except Exception as e:
#         UtilityFunctions.logScreenMsg(f"Connection failed: {e}")
#         schedule_reconnect()

# # Start the first connection attempt
# connect_to_server()



def modbus_polling_loop():
    while True:
        try:
            ModbusLibcls.GetStopWatchStatus()
            # UtilityFunctions.logScreenMsg("Connected to server!")
            time.sleep(0.1)  # Wait before next read
        except Exception as e:
            UtilityFunctions.logScreenMsg(f"Connection failed: {e}")
            time.sleep(2)  # Wait before retrying

# Start the loop in a single background thread
polling_thread = threading.Thread(target=modbus_polling_loop, daemon=True)
polling_thread.start()



while True:
    try:
    # Enable For Modbus
    # ModbusLibcls.WriteRegister(1,2)
        # if (ModbusConnectStatus==1):
        #     ModbusLibcls.GetStopWatchStatus()
        # else:
        #     schedule_reconnect()
        #         
        if (RestServicecls.InitStatus==0):
        # else:
        #     Synced_JSONData= null
        #     # RestServicecls.Syncwithonline=1

        # From Rest Server Read all heats in loop  or receive heat from other terminal.
            HeatStatus = StopTimerServicecls.getHeatStatus()
            #print (HeatStatus)
            if (RestServicecls.Synced_JSONData is None):
                RestServicecls.TimerState="Busy"
                RestServicecls.TimerStateMessage= "Waiting for Heat File to be loaded"
            else:
                RestServicecls.TimerState="State"
                RestServicecls.TimerStateMessage= HeatStatus
                # # print (HeatStatus)
                # if ():
                #     RestServicecls.TimerState="Busy"
                #     RestServicecls.TimerStateMessage="Updating Result To Cloud"
                # elif():

                
            
            if ( not RestServicecls.Synced_JSONData is None):
                if (HeatStatus== TimerStatus.WaitingToStart or HeatStatus== TimerStatus.Stoped  ):
                    Logger.app_log.info("waiting to Next Heat Start")
                    HeatID,EventID=RestServicecls.GetNextHeatID(RestServicecls.Synced_JSONData)
                    if (HeatID!="WaitingToStart"):
                        Logger.app_log.info("Loaded Heat "+ str(HeatID))
                        heatDataDisplay = JsonHelper.GetHeatDataDisplay(HeatID,EventID,RestServicecls.Synced_JSONData)
                        if (heatDataDisplay==None):
                            StopTimerServicecls.SetHeatStatus(TimerStatus.Stoped)
                            #print ("is none " + str(HeatID) + str(EventID))
                            RestServicecls.TimerState="Busy"
                            RestServicecls.TimerStateMessage= "no heats found"
                        else:
                            StopTimerServicecls.ResetTimer()
                            StopTimerServicecls.PrepareHeat(heatDataDisplay)
                            StopTimerServicecls.SetHeatStatus(TimerStatus.loadedToStart)
                    else:
                        print ("no heats found")

                elif(HeatStatus== TimerStatus.Completed):            
                    RestServicecls.Synced_JSONData, Heatdata,heatindex,eventIndex= FireBaseHelper.PrepareHeatResultstoLocalJSONDB(HeatID,heatDataDisplay,RestServicecls.Synced_JSONData)

                    RestServicecls.TimerState="Busy"
                    RestServicecls.TimerStateMessage="Updating Result To Cloud"
                    #time.sleep(2)
                    FireBaseHelper.AppendHeatResult(FireBaseHelper.WriteHeatResultsPath,Heatdata)
                    FireBaseHelper.AppendSwimmerResults(FireBaseHelper.WriteSwimmerTablePath,Heatdata)

                    # Commented as taking more time VCR 15-06-25
                    # Enable To Update Each Heat Result
                    FireBaseHelper.UpdateHeatResultToFirebase(Heatdata,heatindex,eventIndex)
                    # To Update Each Heat Result to Swimmer                     
                    #FireBaseHelper.UpdateHeatResultToFirebaseSwimRecord(Heatdata)                    
                    StopTimerServicecls.SetHeatStatus(TimerStatus.WaitingToStart)
                    
                    # Update Resutls to File
                elif ( HeatStatus== TimerStatus.loadedToStart or HeatStatus== TimerStatus.InProgress or HeatStatus==
                TimerStatus.WaitBeforeLoad or HeatStatus== TimerStatus.ResetbeforeStart ):
                    StopTimerServicecls.RunTimer()
        else:
            RestServicecls.TimerState="State"
            RestServicecls.TimerStateMessage= "Waiting for Heat File to be loaded"
    except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
