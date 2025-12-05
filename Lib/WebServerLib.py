import http.server
import socketserver
import os


class WebServerCls: 
    PORT = 8000
    HTTPIP= "0.0.0.0"
    httpd=""

    def init(HTTPIP,PORT):
        web_dir = os.path.join(os.path.dirname(__file__),"templates","Eejo_SwimManagerWeb")
        os.chdir(web_dir)
        Handler = http.server.SimpleHTTPRequestHandler
        WebServerCls.httpd = socketserver.TCPServer((HTTPIP, PORT), Handler)