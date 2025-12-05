#import RPi.GPIO as GPIO
from time import sleep
from Lib.SwimDataHolder import TimerStatus,SwimerBoardDetail,HeatDataDisplay
from Lib.LogerService import Logger
import datetime
import time
from Lib.ModbusLib import ModbusLibcls


# Logger.app_log.info("data")

# Logger.app_log.debug("Harmless debug Message")
# Logger.app_log.info("Just an information")
# Logger.app_log.warning("Its a Warning")
# Logger.app_log.error("Did you try to divide by zero")
# Logger.app_log.critical("Internet is down")

class StopTimerServicecls:
    #Available pins
    #StopWatchInputPins = [15, 14, 18,23,24,25,8,7,1,12,16,20,21]
    #StopWatchInputPins = [23,18,25,24,15,8]
    Startpin=8
    PreviousState=TimerStatus.Stoped
    StopWatchInputPins = [7,20,18,21,22,-1,-1,-1,-1]
    SIDE_A_SwBits = [7,20,18,21,22,22,21,6,4,2,0,0]    

    SIDE_B_SwBits = [-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13]   
    #MODSwitchBits=[22,21,18,20,23,19,7,6,4,2,0]
    # MODSwitchBits=[3,4,2,7,6,22,21,20,18,4,2,0]
    MODSwitchBits=[19,23,18,20,22,21,7,6,4,2,0,0]


    #MODSwitchBits=[6,5,7,3,4,2,22,23,19,21,0,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13]

#    MODSwitchBits=[6,5,7,3,4,2,22,23,19,21,0,-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11,-12,-13]
    latchedBoardList=[]
    ShortLatchTimethrushhold=0
    LongtLatchTimethrushhold=60
    StartTimeValue=0.00
    StopWatchStartPinsStatus=0
    StartLatch=0
    StartLatchCounter=0
    HeatStatus=TimerStatus.Stoped
    heatDataDisplay= HeatDataDisplay()
    StartRestcommand=0
    def ResetTimer():
        Logger.app_log.debug("ResetTimer Started")
        try:
            StopTimerServicecls.StartTimeValue=0.00
            StopTimerServicecls.StopWatchStartPinsStatus=0
            StopTimerServicecls.StartLatch=0
            StopTimerServicecls.StartLatchCounter=0
            StopTimerServicecls.HeatStatus=TimerStatus.Stoped
            for boardnum in range (0,len(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails)):
                print ( "Restet Timer" +str(boardnum))
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=0
                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=0
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return

    def PlayTones(Heatestate):
        RegisterAddress=0
        LowFreqTones= [0,100,740,800,1000, 2300, 2600,3000 ,3100 , 3600,3700, 4100,4200]
#        BoardFreq= [740,800,1000, 2300, 2600,3000 ,3100 , 3600,3700, 4100,4200]
        BoardFreq= [3600,3600,3600,3600,3600,3600,3600,3600,3600,3600,3600]


        if ((Heatestate == TimerStatus.InProgress)):
            for boardnum in range(0,len(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails)):
                if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime==1):                                   
                    if not (boardnum in StopTimerServicecls.latchedBoardList):      # To Avoide Latch sound                   
                        ModbusLibcls.WriteRegisters(RegisterAddress,[BoardFreq[boardnum],0])
                        print( " Playing Board " + str(boardnum))
                        StopTimerServicecls.latchedBoardList.append(boardnum)
    
        if (StopTimerServicecls.PreviousState != Heatestate):
            StopTimerServicecls.latchedBoardList=[]
            StopTimerServicecls.PreviousState=Heatestate
            if (Heatestate == TimerStatus.WaitingToStart):
                # ModbusLibcls.WriteRegisters(RegisterAddress,[LowFreqTones[0],500])
                ModbusLibcls.WriteRegisters(RegisterAddress,[4,500])
                # ModbusLibcls.WriteRegisters(RegisterAddress,[LowFreqTones[0],500])

            # if (Heatestate == TimerStatus.Stoped):
                # ModbusLibcls.WriteRegisters(RegisterAddress,[LowFreqTones[1],200])

            elif (Heatestate == TimerStatus.InProgress):
                ModbusLibcls.WriteRegisters(RegisterAddress,[100,500])

            elif (Heatestate == TimerStatus.Completed):
                ModbusLibcls.WriteRegisters(RegisterAddress,[2300,100])

            elif (Heatestate == TimerStatus.loadedToStart):
                ModbusLibcls.WriteRegisters(RegisterAddress,[4,500])
                # ModbusLibcls.WriteRegisters(RegisterAddress,[LowFreqTones[2],100])

            elif (Heatestate == TimerStatus.WaitBeforeLoad ): 
                ModbusLibcls.WriteRegisters(RegisterAddress,[BoardFreq[0],50])


            # elif (Heatestate == TimerStatus.ResetbeforeStart):
                # ModbusLibcls.WriteRegisters(RegisterAddress,[LowFreqTones[6],500])
            # else

        return

    def PrepareHeat(HeatDataDisplay):
        Logger.app_log.debug("PrepareHeat Started")
        try:
        # PIN Mode Configuration
            #GPIO.setmode(GPIO.BCM)
            StopTimerServicecls.heatDataDisplay= HeatDataDisplay
            #GPIO.setup(StopTimerServicecls.Startpin, GPIO.IN)
            for pinID in range(0,len(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails)):
             #   GPIO.setup(StopTimerServicecls.StopWatchInputPins[pinID], GPIO.IN)
                print("Timer Mode Setting for PIN " + str(StopTimerServicecls.StopWatchInputPins[pinID]) )
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in PrepareHeat %s",  exc_info=ex)
        return

    def time_convert(sec):
        Logger.app_log.debug("time_convert Started")
        try:
            mins = sec // 60
            sec = sec % 60
            hours = mins // 60
            mins = mins % 60
            convertedTime= str(int(hours))+":"+ str(int(mins))+":" + str(round(sec,3))
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in time_convert %s", exc_info=ex)
        return convertedTime

    def getHeatStatus():
        return StopTimerServicecls.HeatStatus

    def SetHeatStatus( HeatvalueToSet):
        StopTimerServicecls.HeatStatus= HeatvalueToSet

    def GetHeatStartTime(StopTimerServicecls):
        return StopTimerServicecls.heatDataDisplay.HeatStartTime

    def RunTimer():
        Logger.app_log.debug("RunTimer Started")
        try:
            # Storing Status of all input pins
            # sleep(0.01)
            # SwitchStatus = [ModbusLibcls.SwitchStatus >> i & 1 for i in range(16 - 1,-1,-1)]
            # SwitchStatus.reverse()
            # print(ModbusLibcls.SwitchStatus)
            # For Start pin
          #  StopTimerServicecls.StopWatchStartPinsStatus =GPIO.input(StopTimerServicecls.Startpin)
            if ( (StopTimerServicecls.MODSwitchBits[0] != 0) and len(ModbusLibcls.StopWatchSwStatus) >0):

                StopTimerServicecls.StopWatchStartPinsStatus = ModbusLibcls.StopWatchSwStatus[StopTimerServicecls.MODSwitchBits[0]]

            if (StopTimerServicecls.StopWatchStartPinsStatus ==1 or StopTimerServicecls.StartRestcommand==1):
                if (StopTimerServicecls.StartRestcommand==1 and StopTimerServicecls.HeatStatus==TimerStatus.loadedToStart ):
                    StopTimerServicecls.StartLatch=1
                    current_date = datetime.datetime.now()
                    StopTimerServicecls.heatDataDisplay.HeatStartTime= int(current_date.strftime("%Y%m%d%H%M%S"))
                     #Reseting cmd variable
                    StopTimerServicecls.StartRestcommand=0

                if (StopTimerServicecls.HeatStatus==TimerStatus.loadedToStart and StopTimerServicecls.StartLatch==0):
                    if (StopTimerServicecls.StartLatchCounter>=StopTimerServicecls.ShortLatchTimethrushhold):
                        StopTimerServicecls.ResetTimer()
                        StopTimerServicecls.StartLatch=1

                        #StopTimerServicecls.HeatStatus!=TimerStatus.InProgress
                        current_date = datetime.datetime.now()
                        StopTimerServicecls.heatDataDisplay.HeatStartTime= int(current_date.strftime("%Y%m%d%H%M%S"))
                        Logger.app_log.info("Start Timer Latched")
                    else:
                        StopTimerServicecls.StartLatchCounter +=1

                elif (StopTimerServicecls.HeatStatus==TimerStatus.WaitBeforeLoad):
                    #StopTimerServicecls.StartLatchCounter = 0
                    StopTimerServicecls.StartLatch=0
                    #Reseting cmd variable
                    #StopTimerServicecls.StartRestcommand=0
                    #StopTimerServicecls.HeatStatus=TimerStatus.Completed
                    StopTimerServicecls.StartLatchCounter +=1
                    if (StopTimerServicecls.StartLatchCounter > 2):
                        StopTimerServicecls.HeatStatus=TimerStatus.ResetbeforeStart

                    elif (StopTimerServicecls.StartRestcommand==1):
                            StopTimerServicecls.HeatStatus=TimerStatus.ResetbeforeStart
                            StopTimerServicecls.StartRestcommand=0


                elif (StopTimerServicecls.HeatStatus==TimerStatus.ResetbeforeStart):
                    StopTimerServicecls.StartLatchCounter=0
                    StopTimerServicecls.StartLatch=0
                    #Reseting cmd variable
                    StopTimerServicecls.StartRestcommand=0
                    StopTimerServicecls.HeatStatus=TimerStatus.Completed
            elif (StopTimerServicecls.StartRestcommand==4):
                current_date = datetime.datetime.now()
                StopTimerServicecls.heatDataDisplay.HeatEndTime=int(current_date.strftime("%Y%m%d%H%M%S"))
                StopTimerServicecls.HeatStatus=TimerStatus.Completed
                StopTimerServicecls.StartRestcommand=0
            else :
                    StopTimerServicecls.StartLatchCounter = 0

    #Checking BoardInout Status
            for boardnum in range(0,len(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails)):
                if (StopTimerServicecls.MODSwitchBits[boardnum+1] !=0 and len(ModbusLibcls.StopWatchSwStatus) >= boardnum+1):
                    StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsStatus = ModbusLibcls.StopWatchSwStatus[StopTimerServicecls.MODSwitchBits[boardnum+1]]

                if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].swimerStatus == 0):
                    #To be Disabled for Win Systems
                    if ( len(ModbusLibcls.StopWatchSwStatus) >=boardnum+1):
                        if (StopTimerServicecls.MODSwitchBits[boardnum+1]==0):
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsStatus=0                    
                        else:                         
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsStatus= ModbusLibcls.StopWatchSwStatus[StopTimerServicecls.MODSwitchBits[boardnum+1]]

                        # StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsStatus = GPIO.input(StopTimerServicecls.StopWatchInputPins[boardnum])
                                        
                     # if no command From REST Consider Pin inputs
                     #1-Pause,2-Continue,3-Disable,4-Bypass
                    if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].RestBoardTimerCmd==0 ):
                        if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsStatus==1):
                            if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter >= StopTimerServicecls.ShortLatchTimethrushhold):
                                #For Debug, Enable this lines for knowing PIN Numbers
                                if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus==0):
                                    if (len(ModbusLibcls.StopWatchSwStatus) >= boardnum+1):
                                        print (str(time.time()) + " BIT - " + str(StopTimerServicecls.MODSwitchBits[boardnum+1]) + " Board " + str(boardnum) +  " Latched")
                                    else:                                        
                                        print (str(time.time()) + " Board " + str(boardnum) + " Latched")

                                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=1
                                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=1
                            else:
                                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter +=1
                        else :
                                StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter = 0
                    elif(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].RestBoardTimerCmd==1 ):
                        if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus==0):
                            if (len(ModbusLibcls.StopWatchSwStatus) >= boardnum+1):
                                print (str(time.time()) + " BIT - " + str(StopTimerServicecls.MODSwitchBits[boardnum+1]) + " Board " + str(boardnum) +  " Latched")
                            else:                                        
                                print (str(time.time()) + " Board " + str(boardnum) + " Latched")

                            # print (str(time.time()) + " BIT - " + str(StopTimerServicecls.MODSwitchBits[boardnum+1]) + "Board " + str(boardnum) +  " Latched")
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=1
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=1
                        
                    elif(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].RestBoardTimerCmd==2 ):
                        if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus==1):
                                #  print (str(time.time()) + " BIT - " + str(StopTimerServicecls.StopWatchInputPins[boardnum]) + "Board " + str(boardnum) +  "Latched")
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=0
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=0 
                    
                    else:
                    #print ("Board Lock"+ str(boardnum))
                    #print( StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].swimerStatus)
                        StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=1
                    #print("Board"+ str(boardnum) +"is locked")
                else:
                    StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime = 1
                    StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].timerValue=0


            # Start Timer
            if (StopTimerServicecls.StartLatch==1):
                # Start Time
                if (StopTimerServicecls.StartTimeValue==0): #Record Starok t Time
                    StopTimerServicecls.StartLatch==1 # TimerStarted Latch
                    StopTimerServicecls.StartTimeValue= round(time.time(),3)
                    print("Timer Startd ")
                    StopTimerServicecls.HeatStatus=TimerStatus.InProgress

                for board in StopTimerServicecls.heatDataDisplay.SwimerBoardDetails:

                    # match board.RestBoardTimerCmd:
                    if(board.RestBoardTimerCmd==0): #1-Pause,2-Continue,3-Disable,4-Bypass
                        if (board.StopWatchInputPinsLatchStatus==1 and board.LockTime==0 ): #board1 timer
                            board.timerValue= round(time.time()-StopTimerServicecls.StartTimeValue,3)
                            print(  "Board "+ str(board.boardId)+ " Time Latched @" + StopTimerServicecls.time_convert(board.timerValue))
                            Logger.app_log.info("Board "+ str(board.boardId)+ " Time Latched @" + StopTimerServicecls.time_convert(board.timerValue))
                            #board.StopWatchInputPinsLatchStatus=0
                            board.LockTime=1
                        elif (board.LockTime==0):
                            board.timerValue= round(time.time()-StopTimerServicecls.StartTimeValue,3)
                    elif(board.RestBoardTimerCmd==1):
                        if (board.LockTime==0):
                            board.timerValue= round(time.time()-StopTimerServicecls.StartTimeValue,3)
                            board.LockTime=1
                    elif(board.RestBoardTimerCmd==2):
                        if ( board.swimerStatus == 0):
                            board.LockTime=0
                            board.timerValue= round(time.time()-StopTimerServicecls.StartTimeValue,3)
                    elif(board.RestBoardTimerCmd==3):
                        board.LockTime=1
                        board.timerValue= 0
                    elif(board.RestBoardTimerCmd==4):                        
                        if ( board.swimerStatus == 0):
                            board.timerValue= round(time.time()-StopTimerServicecls.StartTimeValue,3)

                for board in StopTimerServicecls.heatDataDisplay.SwimerBoardDetails:
                    #print ("board.swimerStatus " + str( board.swimerStatus))
                    if (board.swimerStatus== 0):
                        if (board.LockTime==1):
                            StopTimerServicecls.HeatStatus= TimerStatus.WaitBeforeLoad
                        else:
                            StopTimerServicecls.HeatStatus= TimerStatus.InProgress
                            break
                    else:
                        StopTimerServicecls.HeatStatus= TimerStatus.WaitBeforeLoad

                if (StopTimerServicecls.HeatStatus==TimerStatus.WaitBeforeLoad):
                    #print (StopTimerServicecls.HeatStatus)
                    current_date = datetime.datetime.now()
                    StopTimerServicecls.heatDataDisplay.HeatEndTime=int(current_date.strftime("%Y%m%d%H%M%S"))
            # else:
            # #if(StopTimerServicecls.HeatStatus!=TimerStatus.WaitBeforeLoad):
            #     for board in StopTimerServicecls.heatDataDisplay.SwimerBoardDetails:
            #         board.timerValue= 0
            #         board.StopWatchInputPinsLatchStatus=0
            #         board.LockTime=0

            #print (StopTimerServicecls.HeatStatus)
            StopTimerServicecls.PlayTones(StopTimerServicecls.HeatStatus)

        except Exception as ex:
                Logger.app_log.error("Exception occurred: in RunTimer %s",  exc_info=ex)
        return
       
