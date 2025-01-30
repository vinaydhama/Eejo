from enum import Enum


class TimerStatus (Enum):
    Stoped=0
    WaitingToStart = 1
    InProgress = 2
    Completed = 3
    loadedToStart=4
    WaitBeforeLoad = 5
    ResetbeforeStart=6

# class swimstatus (Enum):
#      OK=0
#      NA=1
#      AB=2
#      DQ=3
#      DNC=4

class SwimerBoardDetail:

    def __init__(self, id,sname,sID,timerval,swimstate,stopPIN,stoplatchcounter,stoplatch,lockTime):
        self.boardId =id
        self.swimmername= sname
        self.swimmerID = sID
        self.timerValue = timerval # HH:MM:SS.S
        self.swimerStatus = swimstate# NA,AB,DQ,DNC
        self.StopWatchInputPinsStatus = stopPIN
        self.StopWatchInputPinsLatchCounter =stoplatchcounter
        self.StopWatchInputPinsLatchStatus =stoplatch
        self.LockTime =lockTime

class MeetHeaderDisplay:
    MeetName = "Name of the Event"
    MeetDate = " eventDate"
    MeetAddress = " eventAddressss"

class HeatDataDisplay:
    eventName = "Boys G-5 50m FS"
    eventID = "Boys G-5 50m FS"
    HeatID = 0
    HeatStartTime=0
    HeatEndTime=0
    SwimerBoardDetails=[]

# s= HeatDataDisplay()
# print (s)