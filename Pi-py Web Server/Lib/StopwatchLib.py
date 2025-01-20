import RPi.GPIO as GPIO
from time import sleep
from Lib.SwimDataHolder import TimerStatus,swimstatus,SwimerBoardDetail
from Lib.LogerService import Logger
import time

# Logger.app_log.info("data")

# Logger.app_log.debug("Harmless debug Message")
# Logger.app_log.info("Just an information")
# Logger.app_log.warning("Its a Warning")
# Logger.app_log.error("Did you try to divide by zero")
# Logger.app_log.critical("Internet is down")

class StopTimerServicecls:
    #[18,25,23,8]
    #[23,18,25,24,15,8]
    #Available pins
    #StopWatchInputPins = [15, 14, 18,23,24,25,8,7,1,12,16,20,21]
    StopWatchInputPins = [23,18,25,24,15,8]
    LatchTimethrushhold=50
    SwimerBoardDetails=[]
    StartTimeValue=0.00
    StopWatchStartPinsStatus=0
    StartLatch=0
    StartLatchCounter=0
    NumberOfBoard =10
    HeatStatus=TimerStatus.Stoped
    HeatStartTime=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    HeatEndTime=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    def ResetTimer(self):
        Logger.app_log.debug("ResetTimer Started")
        try:
            self.SwimerBoardDetails=[]
            self.StartTimeValue=0.00
            self.StopWatchStartPinsStatus=0
            self.StartLatch=0
            self.StartLatchCounter=0
            self.NumberOfBoard =10
            self.HeatStatus=TimerStatus.Stoped
            for boardnum in self.SwimerBoardDetails:
                boardnum.StopWatchInputPinsLatchStatus=0
                boardnum.LockTime=0
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in ResetTimer%s",  exc_info=ex)
        return


    def PrepareHeat(self,Boards,SwimerBoardData):
        Logger.app_log.debug("PrepareHeat Started")
        try:
        # PIN Mode Configuration
            NumberOfBoard= Boards
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.StopWatchInputPins[0], GPIO.IN)
            for pinID in range(1,NumberOfBoard+1):
                self.SwimerBoardDetails.append(SwimerBoardDetail (pinID,"Swname1","sID"+str(pinID) ,0,swimstatus.OK,self.StopWatchInputPins[pinID],0,0,0))
                GPIO.setup(self.StopWatchInputPins[pinID], GPIO.IN)
                print("Timer Mode Setting for PIN " + str(self.StopWatchInputPins[pinID]) )
        except Exception as ex:
            Logger.app_log.error("Exception occurred: in PrepareHeat %s",  exc_info=ex)
        return


    def time_convert(self,sec):
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

    def getHeatStatus(self):
        return self.HeatStatus

    def SetHeatStatus(self, HeatvalueToSet):
        self.HeatStatus= HeatvalueToSet
    def GetHeatStartTime(self):
        return self.HeatStartTime

    def GetHeatEndTime(self):
        return self.HeatEndTime

    def GetSwimboardDetails(self):
        return self.SwimerBoardDetails



    # PrepareHeat(4,"")
    # SwimerBoardDetails[0].swimerStatus=swimstatus.NA

    # while True:
    def RunTimer(self):
        Logger.app_log.debug("RunTimer Started")
        try:
            # Storing Status of all input pins
            sleep(0.01)
            # For Start pin
            self.StopWatchStartPinsStatus =GPIO.input(self.StopWatchInputPins[0])
            if (GPIO.input(self.StopWatchInputPins[0])==1 and self.HeatStatus!=TimerStatus.Completed):
                if (self.StartLatchCounter>=self.LatchTimethrushhold):
                    self.StartLatch=1
                    self.HeatStartTime= time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                    Logger.app_log.info("Start Timer Latched")
                else:
                    self.StartLatchCounter +=1
            else :
                    self.StartLatchCounter = 0

            # if (StartLatch==1 and  HeatStatus==TimerStatus.Completed ):
    #             for board in SwimerBoardDetails:
    #                 board.LockTime=0


            for boardnum in range(0,len(self.SwimerBoardDetails)):

                if (self.SwimerBoardDetails[boardnum].swimerStatus == swimstatus.OK):
                    if (GPIO.input(self.StopWatchInputPins[boardnum+1])==1):
                        if (self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter>=self.LatchTimethrushhold):
                            #For Debug, Enable this lines for knowing PIN Numbers
                            # if (self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus==0):
#                                 print (str(time.time()) + "PIN - " + str(self.StopWatchInputPins[boardnum+1]) + "Board " + str(boardnum) +  "Latched")
                            self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=1

                        else:
                            self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter +=1
                    else :
                             self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter = 0
                else:
    #                 print(boardnum)
                    self.SwimerBoardDetails[boardnum].LockTime=1
                    #print("Board"+ str(boardnum) +"is locked")

            # For Force Start
    #         StopWatchStartPinsStatus=1

            # Start Timer
            if (self.StartLatch==1):
                # Start Time
                if (self.StartTimeValue==0): #Record Start Time
                    self.StartLatch==1 # TimerStarted Latch
                    self.StartTimeValue= time.time()
                    print("Timer Startd ")
                    self.HeatStatus=TimerStatus.InProgress

                for board in self.SwimerBoardDetails:
                    if (board.StopWatchInputPinsLatchStatus==1 and board.LockTime==0 ): #board1 timer
                        board.timerValue= time.time()- self.StartTimeValue
                        print(  "Board "+ str(board.boardId)+ " Time Latched @" + self.time_convert(board.timerValue))
                        Logger.app_log.info("Board "+ str(board.boardId)+ " Time Latched @" + self.time_convert(board.timerValue))
                        #board.StopWatchInputPinsLatchStatus=0
                        board.LockTime=1
                    else:
                        board.timerValue= time.time()-self.StartTimeValue;

                for board in self.SwimerBoardDetails:
                    if (board.swimerStatus!= 0):
                        if (board.LockTime==1):
                             self.HeatStatus= TimerStatus.Completed
                        else :
                             self.HeatStatus= TimerStatus.InProgress
                             break
                    else:
                        self.HeatStatus= TimerStatus.Completed

                if (self.HeatStatus==TimerStatus.Completed):
                    print (self.HeatStatus)
                    self.HeatEndTime=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            else:
                for board in self.SwimerBoardDetails:
                    board.timerValue= 0
                    board.StopWatchInputPinsLatchStatus=0
                    board.LockTime=0

#                 print("Timer Not Started or stoped")
                #self.HeatStatus= TimerStatus.Stoped
                print (self.HeatStatus)

        except Exception as ex:
                Logger.app_log.error("Exception occurred: in RunTimer %s",  exc_info=ex)
        return