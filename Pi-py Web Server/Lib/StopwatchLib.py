import RPi.GPIO as GPIO
from time import sleep
import time

class StopTimerServicecls:


    #StopWatchInputPins = [15, 14, 18,23,24,25,8,7,1,12,16,20,21] Available pins
    #StopWatchInputPins = [16,1,12,7,8,25,24,23,18,15,14] # 16 is Start Timer remaining Stop Timers # 12 not going Low
    StopWatchInputPins = [14,15,18,8,23,7,25] # 16 is Start Timer remaining Stop Timers # 12 not going Low
    #
    TimerValues= [0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00,0.00] # Ten Timers
    StopWatchInputPinsStatus =[0,0,0,0,0,0,0,0,0,0,0,0]
    StopWatchInputPinsLatchStatus =[0,0,0,0,0,0,0,0,0,0,0,0]
    NumberOfBoard =6
    def configPins(Boards):
        # PIN Mode Configuration
        StopTimerServicecls.NumberOfBoard= Boards
        GPIO.setmode(GPIO.BCM)
        for pinID in range(StopTimerServicecls.NumberOfBoard+1):
            GPIO.setup(StopTimerServicecls.StopWatchInputPins[pinID], GPIO.IN)
            print("Timer Mode Setting for PIN " + str(StopTimerServicecls.StopWatchInputPins[pinID]) )
        return

    def time_convert(sec):
        mins = sec // 60
        sec = sec % 60
        hours = mins // 60
        mins = mins % 60
        convertedTime= str(int(hours))+":"+ str(int(mins))+":" + str(round(sec,3))
        #print(convertedTime)
        #print("Time Lapsed = {0}:{1}:{2}".format(int(hours),int(mins),sec))
        return convertedTime


    def ReadStopWatchTimer():

       #  while True:
        try:
            # Storing Status of all input pins
            sleep(0.01)
            for inpinNum in range(StopTimerServicecls.NumberOfBoard+1):
                StopTimerServicecls.StopWatchInputPinsStatus[inpinNum] = GPIO.input(StopTimerServicecls.StopWatchInputPins[inpinNum])

            # For Force Start
            StopTimerServicecls.StopWatchInputPinsStatus[0]=1
                # For Debuging
                # if (StopWatchInputPinsStatus[inpinNum]==1):
        #                  print("Switch  " + str(StopWatchInputPins[inpinNum] )+ " is ON")
        #             print("Reading Input Status" + str(inpinNum) )


            # Start Timer
            if (StopTimerServicecls.StopWatchInputPinsStatus[0]==1):
                # Start Time


                if (StopTimerServicecls.TimerValues[0]==0): #Record Start Time
                    StopTimerServicecls.StopWatchInputPinsLatchStatus[0]==1 # TimerStarted Latch
                    StopTimerServicecls.TimerValues[0]= time.time()
                    print("Timer Startd "  )

                #TimerValues[0]= time.time()-TimerValues[0];
                #print (time.time()-TimerValues[0])
        #             print(time_convert()

                # if (StopWatchInputPinsStatus[0]==1):
        #                 print("Time " + str(time.time()-TimerValues[0]) )



                # Board 1
                if (StopTimerServicecls.StopWatchInputPinsStatus[1]==1 and StopTimerServicecls.StopWatchInputPinsLatchStatus[1]==0): #board1 timer
                    StopTimerServicecls.StopWatchInputPinsLatchStatus[1]=1
                    StopTimerServicecls.TimerValues[1]= time.time()- StopTimerServicecls.TimerValues[0]
                    print("latch Time-1 " + StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[1]))

                elif(StopTimerServicecls.StopWatchInputPinsLatchStatus[1]==0):
                    StopTimerServicecls.TimerValues[1]= time.time()-StopTimerServicecls.TimerValues[0];
                    #print("board-1 " + time_convert(TimerValues[1]))


                 # Board 2
                if (StopTimerServicecls.StopWatchInputPinsStatus[2]==1 and StopTimerServicecls.StopWatchInputPinsLatchStatus[2]==0 ): #board1 timer
                    StopTimerServicecls.StopWatchInputPinsLatchStatus[2]=1
                    StopTimerServicecls.TimerValues[2]= time.time()- StopTimerServicecls.TimerValues[0]
                    print("latch Time-2 " + StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[2]))
                elif(StopTimerServicecls.StopWatchInputPinsLatchStatus[2]==0):
                    StopTimerServicecls.TimerValues[2]= time.time()-StopTimerServicecls.TimerValues[0];
                    #print("board-2 " + time_convert(TimerValues[2]))


                #print("board-2 " + time_convert(TimerValues[2]))

                 # Board 3
                if (StopTimerServicecls.StopWatchInputPinsStatus[3]==1 and StopTimerServicecls.StopWatchInputPinsLatchStatus[3]==0): #board1 timer
                    StopTimerServicecls.StopWatchInputPinsLatchStatus[3]=1
                    StopTimerServicecls.TimerValues[3]= time.time()- StopTimerServicecls.TimerValues[0]
                    print("latch Time-3 " + StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[3]))
                elif(StopTimerServicecls.StopWatchInputPinsLatchStatus[3]==0):
                    StopTimerServicecls.TimerValues[3]= time.time()-StopTimerServicecls.TimerValues[0];
                    #print("board-3 " + time_convert(TimerValues[3]))


                #print("board-3 " + time_convert(TimerValues[1]))

                # Board 4
                if (StopTimerServicecls.StopWatchInputPinsStatus[4]==1 and StopTimerServicecls.StopWatchInputPinsLatchStatus[4]==0 ): #board1 timer
                    StopTimerServicecls.StopWatchInputPinsLatchStatus[4]=1
                    StopTimerServicecls.TimerValues[4]= time.time()- StopTimerServicecls.TimerValues[0]
                    print("latch Time -4 " + StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[4]))
                elif(StopTimerServicecls.StopWatchInputPinsLatchStatus[4]==0):
                    StopTimerServicecls.TimerValues[4]= time.time()-StopTimerServicecls.TimerValues[0];
                    #print("board-4 " + time_convert(TimerValues[4]))


              #  print("board-4 " + time_convert(TimerValues[1]))

                 # Board 5
                if (StopTimerServicecls.StopWatchInputPinsStatus[5]==1 and StopTimerServicecls.StopWatchInputPinsLatchStatus[5]==0): #board1 timer
                    StopTimerServicecls.StopWatchInputPinsLatchStatus[5]==1
                    StopTimerServicecls.TimerValues[5]= time.time()- StopTimerServicecls.TimerValues[0]
                    print("latch Time -5 " + StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[5]))
                elif(StopTimerServicecls.StopWatchInputPinsLatchStatus[5]==0):
                    StopTimerServicecls.TimerValues[5]= time.time()-StopTimerServicecls.TimerValues[0];
                    #print("board-5 " + time_convert(TimerValues[5]))


               # print("board-5 " + time_convert(TimerValues[1]))

                 # Board 6
                if (StopTimerServicecls.StopWatchInputPinsStatus[6]==1 and StopTimerServicecls.StopWatchInputPinsLatchStatus[6]==0 ): #board1 timer
                    StopTimerServicecls.StopWatchInputPinsLatchStatus[6]=1
                    StopTimerServicecls.TimerValues[6]= time.time()- StopTimerServicecls.TimerValues[0]
                    print("latch Time -6" + StopTimerServicecls.time_convert(StopTimerServicecls.TimerValues[6]))
                elif(StopTimerServicecls.StopWatchInputPinsLatchStatus[6]==0):
                    StopTimerServicecls.TimerValues[6]= time.time()-StopTimerServicecls.TimerValues[0];
                    #print("board-6 " + time_convert(TimerValues[6]))

            else:
                    # Reseting all timers
                    for StopTimerServicecls.TimerNumber in range(StopTimerServicecls.NumberOfBoard):
                        StopTimerServicecls.TimerValues[TimerNumber]= 0
                    #clear all latches
                    for StopTimerServicecls.TimerNumber in range(StopTimerServicecls.NumberOfBoard):
                        StopTimerServicecls.StopWatchInputPinsLatchStatus[TimerNumber]= 0
                    print("Timer Not Started or stoped")


        except:
            print("Something went wrong")

        return




