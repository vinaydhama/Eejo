
import minimalmodbus
import serial
import platform
from Lib.UtilityFunctions import UtilityFunctions
from Lib.LogerService import Logger

class ReconnectError(Exception):
    pass


class ModbusLibcls:
    SwitchStatus1 = 0
    SwitchStatus2 = 0
    SwitchStatus3 = 0
    SwitchStatus4 = 0
    StopWatchSwStatus = []
    regval = []
    instrument = None

    def ConnecttoDevice(ConnectionParams):
        """
        ConnectionParams must include:
          - "COM_Windows": str (e.g., "COM6")
          - "COM_Pi": str (e.g., "/dev/ttyUSB0")
          - "SlaveID": int
          - "Baud": int
          - "bytesize": int  (usually 8)
          - "Parity": enum   (e.g., serial.PARITY_NONE / EVEN / ODD)
          - "mode": int      (minimalmodbus.MODE_RTU or MODE_ASCII)
          - "stopbits": int  (usually 1)
        """
        if platform.system() == "Windows":
            ModbusPortID = ConnectionParams["COM_Windows"]
        else:
            ModbusPortID = ConnectionParams["COM_Pi"]

        ModbusLibcls.initModbusdevice(
            ModbusPortID,
            ConnectionParams["SlaveID"],
            ConnectionParams["Baud"],
            ConnectionParams["bytesize"],
            ConnectionParams["Parity"],
            ConnectionParams["mode"],
            ConnectionParams["stopbits"],
        )

    def initModbusdevice(port, slave_id, baudrate, bytesize, parity, mode, stopbits):
        try:
            ModbusLibcls.instrument = minimalmodbus.Instrument(port=port, slaveaddress=slave_id)
            ModbusLibcls.instrument.serial.baudrate = baudrate
            ModbusLibcls.instrument.serial.bytesize = bytesize
            # parity=serial.PARITY_NONE
            ModbusLibcls.instrument.serial.parity = parity
            # mode=minimalmodbus.MODE_RTU
            ModbusLibcls.instrument.mode = mode
            ModbusLibcls.instrument.serial.stopbits = stopbits
            ModbusLibcls.instrument.serial.timeout = 0.5
            UtilityFunctions.logScreenMsg(
                f"Connect Params: port={port}, slave_id={slave_id}, baudrate={baudrate}, "
                f"bytesize={bytesize}, parity={parity}, mode={mode}, stopbits={stopbits}"
            )
            UtilityFunctions.logScreenMsg("Modbus instrument created")
        except Exception as e:
            UtilityFunctions.logScreenMsg("Could not connect to device via " + port)
            Logger.app_log.exception(f"initModbusdevice: {e}")


    def GetStopWatchStatus():
        """
        Reads 4 x 16-bit switch status words (if your device maps them).
        The current implementation reads registers [0..6] and maps two words (index 4 and 3),
        then builds a bit-array StopWatchSwStatus (LSB first after reverse()).
        """
        try:
            ModbusLibcls.ReadModbusData(3)  # '3' is not used inside current implementation
            # Build bit arrays from 4 words (here only word1/2 are filled)
            words = [ModbusLibcls.SwitchStatus4, ModbusLibcls.SwitchStatus3,
                     ModbusLibcls.SwitchStatus2, ModbusLibcls.SwitchStatus1]
            bits = []
            for w in words:
                bits.extend([(w >> i) & 1 for i in range(16 - 1, -1, -1)])
            bits.reverse()
            ModbusLibcls.StopWatchSwStatus = bits
        except Exception as e:
            UtilityFunctions.logScreenMsg("Unable to Read Register")
            Logger.app_log.exception(f"GetStopWatchStatus: {e}")
            # raise ReconnectError("Failed to connect to server.") from e

    def WriteRegisters(Regaddress, valuetoWrite):
        try:
            ModbusLibcls.instrument.write_registers(Regaddress, valuetoWrite)
        except Exception as e:
            Logger.app_log.exception(f"WriteRegisters: {e}")
            UtilityFunctions.logScreenMsg("Unable to Write Register")

    def ReadModbusData(regaddress):
        """
        Read a block of holding registers (device-dependent).
        Currently reads 7 registers from address 0 and maps switch words.
        Adjust as per your device map if needed.
        """
        try:
            ModbusLibcls.regval = ModbusLibcls.instrument.read_registers(0, 7)
            # Map words according to your device layout
            ModbusLibcls.SwitchStatus1 = ModbusLibcls.regval[4]
            ModbusLibcls.SwitchStatus2 = ModbusLibcls.regval[3]
            # If your device actually provides words 3 & 4, map them here:
            # ModbusLibcls.SwitchStatus3 = ModbusLibcls.regval[2]
            # ModbusLibcls.SwitchStatus4 = ModbusLibcls.regval[1]
        except minimalmodbus.NoResponseError as e:
            UtilityFunctions.logScreenMsg("Modbus: no response")
            Logger.app_log.exception(f"ReadModbusData: {e}")

            # raise ReconnectError("Failed to connect to server.") from e
        except Exception as e:
            # Any other I/O error
            UtilityFunctions.logScreenMsg(f"Modbus read error: {e}")
            Logger.app_log.exception(f"ReadModbusData: {e}")

