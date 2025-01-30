import RPi.GPIO as GPIO
from time import sleep
import time
StopWatchInputPins = [8,25,1,16,12,7]
#StopWatchInputPins = [15, 14, 18,23,24,25,8,7,1,12,16,20,21] #Available pins
#StopWatchInputPins = [16,1,12,7,8,25,24,23,18,15,14] # 16 is Start Timer remaining Stop Timers # 12 not going Low
#StopWatchInputPins = [15,18,8,23,7,25] # 16 is Start Timer remaining Stop Timers # 12 not going Low
#
TimerValues= [0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00] # Ten Timers
StopWatchInputPinsStatus =[0,0,0,0,0,0,0,0,0,0,0,0]
StopWatchInputPinsLatchStatus =[0,0,0,0,0,0,0,0,0,0,0,0]
NumberOfBoard =5


def time_convert(sec):
  mins = sec // 60
  sec = sec % 60
  hours = mins // 60
  mins = mins % 60
  convertedTime= str(int(hours))+":"+ str(int(mins))+":" + str(round(sec,3))
  print(convertedTime)
  #print("Time Lapsed = {0}:{1}:{2}".format(int(hours),int(mins),sec))
  return convertedTime


# PIN Mode Configuration

GPIO.setmode(GPIO.BCM)
for pinID in range(NumberOfBoard+1):
    GPIO.setup(StopWatchInputPins[pinID], GPIO.IN)
    print("Timer Mode Setting for PIN " + str(StopWatchInputPins[pinID]) )

def StopWatchTimer():
        return TimeValue
while True:
#     try:
        # Storing Status of all input pins
        sleep(1)
        for inpinNum in range(NumberOfBoard+1):
            StopWatchInputPinsStatus[inpinNum] = GPIO.input(StopWatchInputPins[inpinNum])
            if (StopWatchInputPinsStatus[inpinNum]==1):
                print(str(time.time())+" switch  " + str(StopWatchInputPins[inpinNum] )+ " is on")


    #     for boardnum in range(1,len(self.SwimerBoardDetails)):

#                 if (self.SwimerBoardDetails[boardnum].swimerStatus == swimstatus.OK):
#                     if (GPIO.input(self.StopWatchInputPins[boardnum+1])==1):
#                         if (self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter>=self.LatchTimethrushhold):
                          #  print ("Board " + str(self.StopWatchInputPins[0]))
#                             self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchStatus=1
#                         else:
#                             self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter +=1
#                     else :
#                             self.SwimerBoardDetails[boardnum].StopWatchInputPinsLatchCounter = 0
#                 else:
                    #print(boardnum)
#                     self.SwimerBoardDetails[boardnum].LockTime=1

            # For Debuging
#         if (stopwatchinputpinsstatus[inpinnum]==1):
#              print("switch  " + str(stopwatchinputpins[inpinnum] )+ " is on")
#             print("Reading Input Status" + str(inpinNum) )