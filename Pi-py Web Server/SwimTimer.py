from flask import Flask, jsonify,Response,json,render_template
import threading
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
  #print(convertedTime)
  #print("Time Lapsed = {0}:{1}:{2}".format(int(hours),int(mins),sec))
  return convertedTime


def StopWatchTimer():

    while True:
        try:
            # Storing Status of all input pins
            sleep(0.01)
            for inpinNum in range(NumberOfBoard+1):
                StopWatchInputPinsStatus[inpinNum] = GPIO.input(StopWatchInputPins[inpinNum])

            # For Force Start
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

                #TimerValues[0]= time.time()-TimerValues[0];
                #print (time.time()-TimerValues[0])
        #             print(time_convert()

                # if (StopWatchInputPinsStatus[0]==1):
        #                 print("Time " + str(time.time()-TimerValues[0]) )



                # Board 1
                if (StopWatchInputPinsStatus[1]==1 and StopWatchInputPinsLatchStatus[1]==0): #board1 timer
                    StopWatchInputPinsLatchStatus[1]=1
                    TimerValues[1]= time.time()- TimerValues[0]
                    print("latch Time-1 " + time_convert(TimerValues[1]))

                elif(StopWatchInputPinsLatchStatus[1]==0):
                    TimerValues[1]= time.time()-TimerValues[0];
                    #print("board-1 " + time_convert(TimerValues[1]))


                 # Board 2
                if (StopWatchInputPinsStatus[2]==1 and StopWatchInputPinsLatchStatus[2]==0 ): #board1 timer
                    StopWatchInputPinsLatchStatus[2]=1
                    TimerValues[2]= time.time()- TimerValues[0]
                    print("latch Time-2 " + time_convert(TimerValues[2]))
                elif(StopWatchInputPinsLatchStatus[2]==0):
                    TimerValues[2]= time.time()-TimerValues[0];
                    #print("board-2 " + time_convert(TimerValues[2]))


                #print("board-2 " + time_convert(TimerValues[2]))

                 # Board 3
                if (StopWatchInputPinsStatus[3]==1 and StopWatchInputPinsLatchStatus[3]==0): #board1 timer
                    StopWatchInputPinsLatchStatus[3]=1
                    TimerValues[3]= time.time()- TimerValues[0]
                    print("latch Time-3 " + time_convert(TimerValues[3]))
                elif(StopWatchInputPinsLatchStatus[3]==0):
                    TimerValues[3]= time.time()-TimerValues[0];
                    #print("board-3 " + time_convert(TimerValues[3]))


                #print("board-3 " + time_convert(TimerValues[1]))

                # Board 4
                if (StopWatchInputPinsStatus[4]==1 and StopWatchInputPinsLatchStatus[4]==0 ): #board1 timer
                    StopWatchInputPinsLatchStatus[4]=1
                    TimerValues[4]= time.time()- TimerValues[0]
                    print("latch Time -4 " + time_convert(TimerValues[4]))
                elif(StopWatchInputPinsLatchStatus[4]==0):
                    TimerValues[4]= time.time()-TimerValues[0];
                    #print("board-4 " + time_convert(TimerValues[4]))


              #  print("board-4 " + time_convert(TimerValues[1]))

                 # Board 5
                if (StopWatchInputPinsStatus[5]==1 and StopWatchInputPinsLatchStatus[5]==0): #board1 timer
                    StopWatchInputPinsLatchStatus[5]==1
                    TimerValues[5]= time.time()- TimerValues[0]
                    print("latch Time -5 " + time_convert(TimerValues[5]))
                elif(StopWatchInputPinsLatchStatus[5]==0):
                    TimerValues[5]= time.time()-TimerValues[0];
                    #print("board-5 " + time_convert(TimerValues[5]))


               # print("board-5 " + time_convert(TimerValues[1]))

                 # Board 6
                if (StopWatchInputPinsStatus[6]==1 and StopWatchInputPinsLatchStatus[6]==0 ): #board1 timer
                    StopWatchInputPinsLatchStatus[6]=1
                    TimerValues[6]= time.time()- TimerValues[0]
                    print("latch Time -6" + time_convert(TimerValues[6]))
                elif(StopWatchInputPinsLatchStatus[6]==0):
                    TimerValues[6]= time.time()-TimerValues[0];
                    #print("board-6 " + time_convert(TimerValues[6]))

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

    return

# PIN Mode Configuration

GPIO.setmode(GPIO.BCM)
for pinID in range(NumberOfBoard+1):
    GPIO.setup(StopWatchInputPins[pinID], GPIO.IN)
    print("Timer Mode Setting for PIN " + str(StopWatchInputPins[pinID]) )



data = 'foo'
host_name = "0.0.0.0"
port = 5002
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('LiveDisplayPage.html')

@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():


    #CORS(app)
    tasks = [
        {
            'id': 1,
            'SwimmerName': u'Name1',
            'swmTimeing': time_convert(TimerValues[1]),
            'myRank': 1
        },
        {
            'id': 2,
            'SwimmerName': u'Name2',
            'swmTimeing': time_convert(TimerValues[2]),
            'myRank': 2
        },
        {
            'id': 3,
            'SwimmerName': u'Name3',
            'swmTimeing': time_convert(TimerValues[3]),
            'myRank': 3
        },
        {
            'id': 4,
            'SwimmerName': u'Name4',
            'swmTimeing': time_convert(TimerValues[4]),
            'myRank': 1
        },
        {
            'id': 5,
            'SwimmerName': u'Name5',
            'swmTimeing': time_convert(TimerValues[5]),
            'myRank': 1
        },
    ]


    	# !return Response(json.dumps(appData), mimetype="application/json",
# 		!headers={"Content-disposition": "attachment"})
    response =  jsonify({'tasks': tasks})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=False, use_reloader=False)).start()
StopWatchTimer()