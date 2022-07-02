import socket
import sys

class Config():
    #APP =''
    def __init__(self,APP=''):
        self.DEBUG = False
        self.COLUMNS ='id,command,parameters,workingdirectory,fullpath'
        self.LISTSELECT = "type=2"
        self.LISTSELECT = "type=2 and fullpath like '\\\\19:30 Corporate Cleanup\\\\*'"
        self.UPDATE = True
        self.SC_COMMANDS = ['<JDE_Solution_Connector.3>']
        if socket.gethostname().lower() in  ['idc2-tes-1','lenovo10','win10desktop','phstidal2']:
            self.TIDAL_CM =  "http://192.168.1.53:8080/api/tes-6.5"
            self.CM_USER = "kooi\dkooi"
            self.CM_PASSWORD= "dkk"
            self.CM_PASSWORD = "WNT{"
        if socket.gethostname() == 'DESKTOP-P3DSN5H':
            self.TIDAL_CM =  "http://usvgatagad002.onetakeda.com:8080/api/tesUSDev"
            self.CM_USER = r'onetakeda\lhq4285'
            self.CM_PASSWORD =  b'O<{OpZe&blZ*D9yFfuX'        #b'Ol5CwVQyqiVR$SuFfuU'

