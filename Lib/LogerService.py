import logging
from logging.handlers import RotatingFileHandler
import time
import os
from pathlib import Path


class Logger:
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    s=time.gmtime()
    # p = Path(__file__).parent.absolute()
    # txt_dir = (p / '../Lib/Eejo_Log').resolve()
    parentpath = os.path.dirname(Path(__file__).parent.absolute())
    LogFileName = os.path.join(parentpath,"Lib","Eejo_Log","Eejo_Timer_"+ time.strftime("%Y_%m_%d_%H_%M_%S", s) +".log")

    # LogFileName= str(txt_dir).lower()+ "/Eejolog"+ time.strftime("%Y_%m_%d_%H_%M_%S", s)
    my_handler = RotatingFileHandler(LogFileName, mode='w', maxBytes=5*1024*1024,
                                     backupCount=2, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.DEBUG)

    app_log = logging.getLogger('root')
    app_log.setLevel(logging.INFO)

    app_log.addHandler(my_handler)

# currentpath = pathlib.Path().resolve()
# print("path is")
# print (currentpath)