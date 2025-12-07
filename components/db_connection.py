import pymysql
from datetime import datetime

attributes = ['id' ,'temperature', 'humidity', "tvoc", "co2", "pm25", "time", "status"]

class MySQL:

    def __init__(self, host='localhost', port=3306, user='root', passwd='root', db='sensor_data'):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.db = db
        self.database = None
        self.last_status = None
        self.now_status = None

    def connect(self):
        try:
            self.database = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                passwd=self.passwd,
                charset='utf8',
                db=self.db,
                autocommit=True
            )
            print('資料庫連接成功')
            return True
        except Exception as e:
            print('資料庫連接錯誤: ' + str(e))
            return False

    def close(self):
        try:
            if self.database:
                self.database.close()
                print("資料庫已關閉連接")
        except Exception as e:
            print("關閉資料庫連接錯誤: " + str(e))

    def insert(self, temperature, humidity, tvoc, co2, pm25, status):
        """插入感測器資料到資料庫"""
        try:
            # 修正 SQL 語法，加入所有欄位
            query = """INSERT INTO data (temperature, humidity, tvoc, co2, pm25, status, time) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            
            current_time = datetime.now()
            
            with self.database.cursor() as cursor:
                cursor.execute(query, (temperature, humidity, tvoc, co2, pm25, status, current_time))
                
            print(f"資料已插入資料庫: T={temperature}°C, H={humidity}%, PM2.5={pm25}")
            return True
            
        except Exception as e:
            print(f"資料庫插入錯誤: {e}")
            return False

    def get_latest_data(self, limit=1):
        """取得最新的感測器資料"""
        try:
            with self.database.cursor() as cursor:
                query = "SELECT * FROM data ORDER BY time DESC LIMIT %s"
                cursor.execute(query, (limit,))
                result = cursor.fetchall()
                return result
        except Exception as e:
            print(f"取得資料錯誤: {e}")
            return None

    def is_status_changed(self):
        """檢查狀態是否改變"""
        try:
            latest_data = self.get_latest_data(2)
            if len(latest_data) >= 2:
                new_status = latest_data[0][attributes.index('status')]
                last_status = latest_data[1][attributes.index('status')]
                return new_status != last_status
            return False
        except Exception as e:
            print(f"檢查狀態變更錯誤: {e}")
            return False
    
    def get_status(self):
        """取得最新的狀態"""
        try:
            latest_data = self.get_latest_data(1)
            if latest_data:
                status = latest_data[0][attributes.index('status')]
                return status
            return None
        except Exception as e:
            print(f"取得狀態錯誤: {e}")
            return None

    def is_connected(self):
        """檢查資料庫連線狀態"""
        try:
            if self.database:
                self.database.ping(reconnect=True)
                return True
            return False
        except Exception:
            return False