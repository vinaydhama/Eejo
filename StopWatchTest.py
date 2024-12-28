import RPi.GPIO as GPIO
from time import sleep
import time

#StopWatchInputPins = [15, 14, 18,23,24,25,8,7,1,12,16,20,21] Available pins
#StopWatchInputPins = [16,1,12,7,8,25,24,23,18,15,14] # 16 is Start Timer remaining Stop Timers # 12 not going Low
StopWatchInputPins = [14,15,18,8,23,7,25] # 16 is Start Timer remaining Stop Timers # 12 not going Low
#
TimerValues= [0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00] # Ten Timers
StopWatchInputPinsStatus =[0,0,0,0,0,0,0,0,0,0,0,0]
StopWatchInputPinsLatchStatus =[0,0,0,0,0,0,0,0,0,0,0,0]
NumberOfBoard =6


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
    try:
        # Storing Status of all input pins
        sleep(0.01)
        for inpinNum in range(NumberOfBoard+1):
            StopWatchInputPinsStatus[inpinNum] = GPIO.input(StopWatchInputPins[inpinNum])

        StopWatchInputPinsStatus[0]=1
            # For Debuging
            # if (StopWatchInputPinsStatus[inpinNum]==1):
#                  print("Switch  " + str(StopWatchInputPins[inpinNum] )+ " is ON")
#             print("Reading Input Status" + str(inpinNum) )


        # Start Timer
        if (StopWatchInputPinsStatus[0]==1):
            # Start Time


            if (TimerValues[0]==0): #Record Start Time
                StopWatchInputPinsLatchStatus[0]==1 # TimerStarted Latch
                TimerValues[0]= time.time()
                print("Timer Startd "  )

            TimerValues[0]= time.time()-TimerValues[0];

            print(TimerValues[0])

            # if (StopWatchInputPinsStatus[0]==1):
#                 print("Time " + str(time.time()-TimerValues[0]) )



            # Board 1
            if (StopWatchInputPinsStatus[1]==1 and TimerValues[1]==0 ): #board1 timer
                StopWatchInputPinsLatchStatus[1]==1
                TimerValues[1]= time.time()- TimerValues[0]
                print("board-1 " + str(timervalues[0]))

#            print("board-1 " + time_convert(TimerValues[1]))


             # Board 2
            if (StopWatchInputPinsStatus[2]==1 and TimerValues[2]==0 ): #board1 timer
                StopWatchInputPinsLatchStatus[2]==1
                TimerValues[2]= time.time()- TimerValues[0]
                print("board-2 " + str(timervalues[0]))

 #           print("board-2 " + time_convert(TimerValues[2]))

             # Board 3
            if (StopWatchInputPinsStatus[3]==1 and TimerValues[3]==0 ): #board1 timer
                StopWatchInputPinsLatchStatus[3]==1
                TimerValues[3]= time.time()- TimerValues[0]
                print("board-3 " + str(timervalues[0]))

  #          print("board-3 " + time_convert(TimerValues[1]))

            # Board 4
            if (StopWatchInputPinsStatus[4]==1 and TimerValues[4]==0 ): #board1 timer
                StopWatchInputPinsLatchStatus[4]==1
                TimerValues[4]= time.time()- TimerValues[0]
                print("board-4 " + str(timervalues[0]))

   #         print("board-4 " + time_convert(TimerValues[1]))

             # Board 5
            if (StopWatchInputPinsStatus[4]==1 and TimerValues[4]==0 ): #board1 timer
                StopWatchInputPinsLatchStatus[5]==1
                TimerValues[5]= time.time()- TimerValues[0]
                print("board-5 " + str(timervalues[0]))

  #          print("board-5 " + time_convert(TimerValues[1]))

             # Board 6
            if (StopWatchInputPinsStatus[6]==1 and TimerValues[6]==0 ): #board1 timer
                StopWatchInputPinsLatchStatus[6]==1
                TimerValues[6]= time.time()- TimerValues[0]
                print("board-6 " + str(timervalues[0]))

   #         print("board-6 " + time_convert(TimerValues[1]))

        else:
                # Reseting all timers
                for TimerNumber in range(NumberOfBoard):
                    TimerValues[TimerNumber]= 0
                #clear all latches
                for TimerNumber in range(NumberOfBoard):
                    StopWatchInputPinsLatchStatus[TimerNumber]= 0
                print("Timer Not Started or stoped")
    except:
        print("Something went wrong")
    #finally:
        #print("The 'try except' is finished")