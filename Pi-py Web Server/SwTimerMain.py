from Lib.StopwatchLib import StopTimerServicecls
from Lib.RestServicesLib import RestServicecls
import threading


#while True:
StopTimerServicecls.configPins(5)
threading.Thread(target=lambda: RestServicecls.app.run(host=RestServicecls.host_name, port=RestServicecls.port, debug=False, use_reloader=False)).start()
while True:
    StopTimerServicecls.ReadStopWatchTimer()

print("Hello")