import logging
from logging.handlers import RotatingFileHandler
import time
class Logger:
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
    s=time.gmtime()
    Filename= "/home/pks/Desktop/Pi-py Web Server/Lib/Log/EejoLogger "+ time.strftime("%Y-%m-%d %H:%M:%S", s)

    my_handler = RotatingFileHandler(Filename, mode='a', maxBytes=5*1024*1024,
                                     backupCount=2, encoding=None, delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(logging.INFO)

    app_log = logging.getLogger('root')
    app_log.setLevel(logging.INFO)

    app_log.addHandler(my_handler)


# while True:
#     Logger.app_log.info("data")
# class Logger:
#     app_log=logging.getLogger('root')
#     def Getlogger():
#         return app_log
#     def SetLogger(self):
# log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')
# s=time.gmtime(1581218900.17436)
# Filename= "/home/pks/Desktop/Pi-py Web Server/Lib/Log/EejoLogger "+ time.strftime("%Y-%m-%d %H:%M:%S", s)


# logFile = 'C:\\Temp\\log'

# my_handler = RotatingFileHandler(Filename, mode='a', maxBytes=5*1024*1024,
#                                  backupCount=2, encoding=None, delay=0)
# my_handler.setFormatter(log_formatter)
# my_handler.setLevel(logging.INFO)

# app_log = logging.getLogger('root')
# app_log.addHandler(my_handler)
# app_log.info("Logging Started")
# return self.app_log

# logger  = Logger()
# x=logger.SetLogger()
# x.info("asa")
# x.info("Logging Started1")
# x.debug("Harmless debug Message")
# Logger.app_log.info("Just an information")

# Logger.app_log.info("data")

# Logger.app_log.debug("Harmless debug Message")
# Logger.app_log.info("Just an information")
# Logger.app_log.warning("Its a Warning")
# Logger.app_log.error("Did you try to divide by zero")
# Logger.app_log.critical("Internet is down")