import RPi.GPIO as GPIO
from time import sleep
from Lib.SwimDataHolder import TimerStatus,SwimerBoardDetail,HeatDataDisplay
from Lib.LogerService import Logger
import datetime
import time

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
    StopWatchInputPins = [25,1,16,12,7]
    ShortLatchTimethrushhold=20
    LongtLatchTimethrushhold=60
    StartTimeValue=0.00
    StopWatchStartPinsStatus=0
    StartLatch=0
    StartLatchCounter=0
    HeatStatus=TimerStatus.Stoped
    heatDataDisplay= HeatDataDisplay()
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

    def PrepareHeat(HeatDataDisplay):
        Logger.app_log.debug("PrepareHeat Started")
        try:
        # PIN Mode Configuration
            GPIO.setmode(GPIO.BCM)
            StopTimerServicecls.heatDataDisplay= HeatDataDisplay
            GPIO.setup(StopTimerServicecls.Startpin, GPIO.IN)
            for pinID in range(0,len(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails)):
                GPIO.setup(StopTimerServicecls.StopWatchInputPins[pinID], GPIO.IN)
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
            sleep(0.01)
            # For Start pin
            StopTimerServicecls.StopWatchStartPinsStatus =GPIO.input(StopTimerServicecls.Startpin)
            if (StopTimerServicecls.StopWatchStartPinsStatus ==1):
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
                    #StopTimerServicecls.HeatStatus=TimerStatus.Completed
                    StopTimerServicecls.StartLatchCounter +=1
                    if (StopTimerServicecls.StartLatchCounter > 20):
                        StopTimerServicecls.HeatStatus=TimerStatus.ResetbeforeStart

                elif (StopTimerServicecls.HeatStatus==TimerStatus.ResetbeforeStart):
                    StopTimerServicecls.StartLatchCounter=0
                    StopTimerServicecls.StartLatch=0
                    StopTimerServicecls.HeatStatus=TimerStatus.Completed
            else :
                    StopTimerServicecls.StartLatchCounter = 0

            for boardnum in range(0,len(StopTimerServicecls.heatDataDisplay.SwimerBoardDetails)):

                if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].swimerStatus == 0):
                    if (GPIO.input(StopTimerServicecls.StopWatchInputPins[boardnum])==1):
                        if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter>=StopTimerServicecls.ShortLatchTimethrushhold):
                            #For Debug, Enable this lines for knowing PIN Numbers
                            if (StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus==0):
                                print (str(time.time()) + "PIN - " + str(StopTimerServicecls.StopWatchInputPins[boardnum]) + "Board " + str(boardnum) +  "Latched")
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=1

                        else:
                            StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter +=1
                    else :
                             StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter = 0
                else:
                    #print ("Board Lock"+ str(boardnum))
                    #print( StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].swimerStatus)
                    StopTimerServicecls.heatDataDisplay.SwimerBoardDetails[boardnum].LockTime=1
                    #print("Board"+ str(boardnum) +"is locked")

            # Start Timer
            if (StopTimerServicecls.StartLatch==1):
                # Start Time
                if (StopTimerServicecls.StartTimeValue==0): #Record Starok t Time
                    StopTimerServicecls.StartLatch==1 # TimerStarted Latch
                    StopTimerServicecls.StartTimeValue= round(time.time(),3)
                    print("Timer Startd ")
                    StopTimerServicecls.HeatStatus=TimerStatus.InProgress

                for board in StopTimerServicecls.heatDataDisplay.SwimerBoardDetails:
                    if (board.StopWatchInputPinsLatchStatus==1 and board.LockTime==0 ): #board1 timer
                        board.timerValue= round(time.time()-StopTimerServicecls.StartTimeValue,3)
                        print(  "Board "+ str(board.boardId)+ " Time Latched @" + StopTimerServicecls.time_convert(board.timerValue))
                        Logger.app_log.info("Board "+ str(board.boardId)+ " Time Latched @" + StopTimerServicecls.time_convert(board.timerValue))
                        #board.StopWatchInputPinsLatchStatus=0
                        board.LockTime=1
                    elif (board.LockTime==0):
                        board.timerValue= round(time.time()-StopTimerServicecls.StartTimeValue,3);

                for board in StopTimerServicecls.heatDataDisplay.SwimerBoardDetails:
                    #print ("board.swimerStatus " + str( board.swimerStatus))
                    if (board.swimerStatus== 0):
                        if (board.LockTime==1):
                             StopTimerServicecls.HeatStatus= TimerStatus.WaitBeforeLoad
                        else :
                             StopTimerServicecls.HeatStatus= TimerStatus.InProgress
                             break
                    else:
                        StopTimerServicecls.HeatStatus= TimerStatus.WaitBeforeLoad

                if (StopTimerServicecls.HeatStatus==TimerStatus.WaitBeforeLoad):
                    #print (StopTimerServicecls.HeatStatus)
                    current_date = datetime.datetime.now()
                    StopTimerServicecls.heatDataDisplay.HeatEndTime=int(current_date.strftime("%Y%m%d%H%M%S"))
            else:
            #if(StopTimerServicecls.HeatStatus!=TimerStatus.WaitBeforeLoad):
                for board in StopTimerServicecls.heatDataDisplay.SwimerBoardDetails:
                    board.timerValue= 0
                    board.StopWatchInputPinsLatchStatus=0
                    board.LockTime=0

            #print (StopTimerServicecls.HeatStatus)

        except Exception as ex:
                Logger.app_log.error("Exception occurred: in RunTimer %s",  exc_info=ex)
        return