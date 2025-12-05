# import socket
# # hostname = input("WWW.Google.com")
# hostname= "LocalHost"

# # IP lookup from hostname
# print(f'The {hostname} IP Address is {socket.gethostbyname(hostname)}')
import time
from datetime import datetime
# import socket
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.connect(("8.8.8.8", 80))
# print(s.getsockname()[0])
# s.close()
class UtilityFunctions:

    def logScreenMsg(msg):
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S') + f".{now.microsecond // 1000:03d}"
        print(f"[{timestamp}] {msg}")
        # print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
