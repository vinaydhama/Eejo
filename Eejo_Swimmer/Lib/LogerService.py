import logging
from logging.handlers import RotatingFileHandler
import time
class Logger:
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    s=time.gmtime()
    Filename= "/home/pks/Desktop/Eejo_Swimmer/Lib/Log/EejoLogger "+ time.strftime("%Y-%m-%d %H:%M:%S", s)

    my_handler = RotatingFileHandler(Filename, mode='a', maxBytes=5*1024*1024,
                                     backupCount=2, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.DEBUG)

    app_log = logging.getLogger('root')
    app_log.setLevel(logging.INFO)

    app_log.addHandler(my_handler)