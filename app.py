from components.plc_connection import PLCConnection
from pymodbus.transaction import ModbusAsciiFramer
import time

plc_info = {
    'framer': ModbusAsciiFramer,
    'port' : "COM3", 
    "stopbits": 1,
    'bytesize': 7,
    'parity': "E",
    'baudrate': 9600
}

def main():
    plc = PLCConnection(framer= plc_info['framer'], port = plc_info['port'], stopbits = plc_info['stopbits'], bytesize = plc_info['bytesize'], parity = plc_info['parity'], baudrate = plc_info['baudrate'])
    plc.connect()

    while True:
        plc.get_data()
        # plc_status = input()
        # if plc_status == 'up':
        #     plc.open()
        # if plc_status == "down":
        #     plc.close()

        time.sleep(1)


if __name__ == "__main__":
    main()