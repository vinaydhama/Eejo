import minimalmodbus
import serial
import time
import platform
from Lib.UtilityFunctions import UtilityFunctions



class ReconnectError(Exception):
    pass


class ModbusLibcls:
    SwitchStatus1=0
    SwitchStatus2=0
    SwitchStatus3=0
    SwitchStatus4=0
    StopWatchSwStatus=[]
    regval=[]
    instrument=0
    # port = 'COM4'
    # slave_id = 1
    def ConnecttoDevice():
        if platform.system() == "Windows":
            ModbusPortID="COM5"
        else:
            ModbusPortID="/dev/ttyUSB0"

        ModbusLibcls.initModbusdevice(ModbusPortID,1,115200,8,serial.PARITY_NONE,1)
        return 


    def initModbusdevice(port,slave_id,baudrate,bytesize,parity,stopbits ):
        try:
            ModbusLibcls.instrument = minimalmodbus.Instrument(port=port, slaveaddress=slave_id)
            # print("Connected to device")
            ModbusLibcls.instrument.serial.baudrate = baudrate
            ModbusLibcls.instrument.serial.bytesize = 8
            ModbusLibcls.instrument.serial.parity = serial.PARITY_NONE
            ModbusLibcls.instrument.mode = minimalmodbus.MODE_RTU
            ModbusLibcls.instrument.serial.stopbits = stopbits
            ModbusLibcls.instrument.serial.timeout = 0.5
            UtilityFunctions.logScreenMsg(
                f"Connect Params: port={port}, slave_id={slave_id}, baudrate={baudrate}, "
                f"bytesize={bytesize}, parity={parity}, stopbits={stopbits}"
)

            print("Instrument created")

        except :
            print("Could not connect to device via "+ port)
           # ModbusLibcls.ConnecttoDevice()
        # sys.exit(1)
    def GetStopWatchStatus():
        try:
            ModbusLibcls.ReadModbusData(3)
            ModbusLibcls.StopWatchSwStatus =[ModbusLibcls.SwitchStatus4 >> i & 1 for i in range(16 - 1,-1,-1)] + [ModbusLibcls.SwitchStatus3 >> i & 1 for i in range(16 - 1,-1,-1)]+            [ModbusLibcls.SwitchStatus2 >> i & 1 for i in range(16 - 1,-1,-1)] + [ModbusLibcls.SwitchStatus1 >> i & 1 for i in range(16 - 1,-1,-1)]
            ModbusLibcls.StopWatchSwStatus.reverse()

        except Exception as  e :
            UtilityFunctions.logScreenMsg( "Unable to Read Register ")
            raise ReconnectError("Failed to connect to server.") from e
            #ModbusLibcls.ConnecttoDevice()


    def WriteRegisters(Regaddress,valuetoWrite):
        try:
            ModbusLibcls.instrument.write_registers(Regaddress,valuetoWrite)
        except :
            print("Unable to Write Register")
           # ModbusLibcls.ConnecttoDevice()


    def ReadModbusData(regaddress):    
        try:
            # ModbusLibcls.SwitchStatus1 = ModbusLibcls.instrument.read_register(regaddress)
            # ModbusLibcls.SwitchStatus2 = ModbusLibcls.instrument.read_register(regaddress+1)

            ModbusLibcls.regval= ModbusLibcls.instrument.read_registers(0,7)
            ModbusLibcls.SwitchStatus1 = ModbusLibcls.regval[4]
            ModbusLibcls.SwitchStatus2 = ModbusLibcls.regval[3]
            # print(ModbusLibcls.regval)
            # ModbusLibcls.SwitchStatus3 = ModbusLibcls.instrument.read_register(regaddress+2)
            # ModbusLibcls.SwitchStatus4 = ModbusLibcls.instrument.read_register(regaddress+3)


            # data = instrument.write_register(10,11)
            # print(ModbusLibcls.SwitchStatus)
        except minimalmodbus.NoResponseError:
            print("Request will fail on first poll")
            raise ReconnectError("Failed to connect to server.") from e

            # time.sleep(2)
