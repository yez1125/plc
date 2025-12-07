from pymodbus.client.serial import ModbusSerialClient
from pymodbus.transaction import ModbusAsciiFramer
from pymodbus.exceptions import ModbusException

class PLCConnection:
    def __init__(self, framer=ModbusAsciiFramer, port = "COM3", stopbits = 1, bytesize = 7, parity = "E", baudrate = 9600):
        self.framer = framer
        self.port = port
        self.stopbits = stopbits
        self.bytesize = bytesize
        self.parity = parity
        self.baudrate = baudrate
        self.client = None
        self.connection = None
    
    def connect(self):
        self.client = ModbusSerialClient(framer= self.framer, port = self.port, stopbits = self.stopbits, bytesize = self.bytesize, parity = self.parity, baudrate = self.baudrate)
        self.connection = self.client.connect()
        print('PLC已連接')

    def get_data(self):
        if self.connection:
        # 每秒抓取PLC資料，並傳送到database
            try:
                values = self.client.read_holding_registers(address=4104, count=21, slave=1).registers
                
                # 將對應的兩個modbus code轉換回hex合起來並取[2:]，在轉換回int
                # temperature 
                temperature = int(hex(values[3])[2:] + hex(values[4])[2:], 16) /10

                # humidity / 10
                humidity = int(hex(values[5])[2:] + hex(values[6])[2:], 16) / 10

                # pm2.5
                pm25 = int(hex(values[7])[2:] + hex(values[8])[2:], 16)
                
                # pm10
                pm10 = int(hex(values[9])[2:] + hex(values[10])[2:], 16)

                # pm2.5 average in one hour
                pm25_average_in_one_hour = int(hex(values[11])[2:] + hex(values[12])[2:], 16)
                
                # pm10 average in one hour
                pm10_average_in_one_hour = int(hex(values[13])[2:] + hex(values[14])[2:], 16)

                # co2
                co2 = int(hex(values[15])[2:] + hex(values[16])[2:], 16)
                
                # tvoc / 1000
                tvoc = int(hex(values[17])[2:] + hex(values[18])[2:], 16) / 1000

            except ModbusException as e:
                print('Error: ' + e)

            print(f"""
temperature: {temperature}
humidity: {humidity}
pm2.5: {pm25}
pm10: {pm10}
pm2.5 average in one hour: {pm25_average_in_one_hour}
pm10 average in one hour: {pm10_average_in_one_hour}
co2: {co2}
tvoc: {tvoc}
""")

            return temperature, humidity, pm25, pm10, pm25_average_in_one_hour, pm10_average_in_one_hour, co2, tvoc

    def change_output(self):
        status = self.client.read_coils(address=1280, count=1, slave=1)
        print(status)
        
    
    def open(self):
        # 如果status改變，則將Y0的狀態改變
        self.client.write_coil(address=1280, value=True, slave=1)

    def close(self):
        self.client.write_coil(address=1280, value=False, slave=1)

    def test_data(self, address):
        if self.connection:
            try:
                data = self.client.read_holding_registers(address=address, count=1, slave=1).registers[0]
            except ModbusException as e:
                print('Error: ' + e)

            return data