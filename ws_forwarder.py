from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymodbus.transaction import ModbusAsciiFramer
from components.plc_connection import PLCConnection
from datetime import datetime
from websocket import create_connection, WebSocketConnectionClosedException
import threading
import asyncio
import time
import json
import random
import socket
from dotenv import load_dotenv
import os

# 載入 .env
load_dotenv()

# WebSocket 伺服器設定
WS_HOST = os.getenv("WS_HOST", "0.0.0.0")
WS_PORT = int(os.getenv("WS_PORT", 8000))

# PLC 設定
plc_info = {
    'framer': ModbusAsciiFramer,
    'port': os.getenv("PLC_PORT", "COM3"),
    'stopbits': int(os.getenv("PLC_STOPBITS", 1)),
    'bytesize': int(os.getenv("PLC_BYTESIZE", 7)),
    'parity': os.getenv("PLC_PARITY", "E"),
    'baudrate': int(os.getenv("PLC_BAUDRATE", 9600))
}

# 遠端 WebSocket 設定
REMOTE_WS_URL = os.getenv(
    "REMOTE_WS_URL",
    "wss://group14.site/ws/NCCU_lab?api_key=machine123&sensor=aq"
)
DEVICE_ID = os.getenv("DEVICE_ID", "aq")
REMOTE_SEND_INTERVAL = int(os.getenv("REMOTE_SEND_INTERVAL", 30))
PING_INTERVAL = 20

app = FastAPI(
    title="AIoT 監控系統 PLC WebSocket Server",
    description="整合 PLC 資料讀取、WebSocket 廣播、遠端轉發與設備控制",
    version="5.0.0"
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 全域變數 ---
plc = None
remote_ws = None
stop_thread = False
main_loop = None
last_remote_send = 0

latest_sensor_data = {
    'temperature': 0,
    'humidity': 0,
    'pm25': 0,
    'pm10': 0,
    'pm25_average': 0,
    'pm10_average': 0,
    'co2': 0,
    'tvoc': 0,
    'timestamp': None,
    'status': 'disconnected'
}

# 儲存所有連線中的 WebSocket client
active_connections: list[WebSocket] = []

# --- WebSocket 連線管理 ---
async def connect_client(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"🔗 本地 WebSocket 連線已建立，目前連線數: {len(active_connections)}")

async def disconnect_client(websocket: WebSocket):
    if websocket in active_connections:
        active_connections.remove(websocket)
    print(f"🔌 本地 WebSocket 連線斷開，目前連線數: {len(active_connections)}")

async def broadcast_data(data: dict):
    """廣播最新資料給所有本地 WebSocket 客戶端"""
    to_remove = []
    for conn in active_connections:
        try:
            await conn.send_json(data)
        except WebSocketDisconnect:
            to_remove.append(conn)
        except Exception as e:
            print(f"❌ 傳送資料給本地客戶端時錯誤: {e}")
            to_remove.append(conn)

    for conn in to_remove:
        if conn in active_connections:
            active_connections.remove(conn)

# --- PLC 初始化與資料收集 ---
def init_plc():
    global plc
    try:
        plc = PLCConnection(
            framer=plc_info['framer'],
            port=plc_info['port'],
            stopbits=plc_info['stopbits'],
            bytesize=plc_info['bytesize'],
            parity=plc_info['parity'],
            baudrate=plc_info['baudrate']
        )
        plc.connect()
        if plc.connection:
            print("✅ PLC 已連線")
            latest_sensor_data['status'] = 'connected'
            return True
        else:
            print("⚠️ PLC 連線失敗")
            latest_sensor_data['status'] = 'plc_disconnected'
            return False
    except Exception as e:
        print(f"⚠️ PLC 連線失敗: {e}")
        latest_sensor_data['status'] = 'plc_disconnected'
        return False

def data_collection_loop():
    """持續讀取 PLC 資料並透過本地 WebSocket 廣播"""
    global stop_thread

    while not stop_thread:
        try:
            if plc and plc.connection:
                sensor_data = plc.get_data()
                if sensor_data:
                    temperature, humidity, pm25, pm10, pm25_avg, pm10_avg, co2, tvoc = sensor_data

                    latest_sensor_data.update({
                        'temperature': temperature,
                        'humidity': humidity,
                        'pm25': pm25,
                        'pm10': pm10,
                        'pm25_average': pm25_avg,
                        'pm10_average': pm10_avg,
                        'co2': co2,
                        'tvoc': tvoc,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'connected'
                    })

                    if main_loop:
                        asyncio.run_coroutine_threadsafe(broadcast_data(latest_sensor_data), main_loop)
            else:
                latest_sensor_data.update({
                    'status': 'plc_disconnected',
                    'timestamp': datetime.now().isoformat()
                })

        except Exception as e:
            print(f"❌ PLC 資料讀取錯誤: {e}")
            latest_sensor_data['status'] = 'error'

        time.sleep(1)

def forward_to_remote():
    """轉發資料到遠端 WebSocket"""
    global remote_ws, last_remote_send, stop_thread
    backoff = 1
    last_ping = 0
    
    while not stop_thread:
        try:
            if remote_ws is None:
                try:
                    print(f"🔄 嘗試連線遠端 WebSocket...")
                    remote_ws = create_connection(REMOTE_WS_URL, timeout=10)
                    print("✅ 遠端 WebSocket 已連線")
                    backoff = 1
                    last_remote_send = 0
                    last_ping = time.time()
                except Exception as e:
                    print(f"⚠️ 遠端 WebSocket 連線失敗: {e}")
                    sleep_time = min(backoff, 60) + random.uniform(0, 0.5)
                    time.sleep(sleep_time)
                    backoff *= 2
                    continue
            
            now = time.time()
            
            # 發送資料
            if now - last_remote_send >= REMOTE_SEND_INTERVAL:
                if latest_sensor_data['status'] == 'connected':
                    payload = json.dumps({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "machine": DEVICE_ID,
                        "values": {
                            "temperature": latest_sensor_data['temperature'],
                            "humidity": latest_sensor_data['humidity'],
                            "pm25": latest_sensor_data['pm25'],
                            "pm10": latest_sensor_data['pm10'],
                            "pm25_average": latest_sensor_data['pm25_average'],
                            "pm10_average": latest_sensor_data['pm10_average'],
                            "co2": latest_sensor_data['co2'],
                            "tvoc": latest_sensor_data['tvoc'],
                        }
                    }, ensure_ascii=False)
                    
                    try:
                        if not getattr(remote_ws, "connected", False):
                            raise WebSocketConnectionClosedException("socket not connected")
                        remote_ws.send(payload)
                        print(f"📤 已轉發到遠端 [{datetime.now().strftime('%H:%M:%S')}]")
                        last_remote_send = now
                    except (WebSocketConnectionClosedException, BrokenPipeError, OSError, socket.timeout) as e:
                        print(f"❌ 轉發失敗: {e}")
                        try:
                            remote_ws.close()
                        except:
                            pass
                        remote_ws = None
                        continue
                else:
                    last_remote_send = now
            
            # 心跳 ping
            if now - last_ping >= PING_INTERVAL and remote_ws is not None:
                try:
                    if getattr(remote_ws, "connected", False):
                        remote_ws.ping()
                        last_ping = now
                except (WebSocketConnectionClosedException, OSError, socket.timeout):
                    try:
                        remote_ws.close()
                    except:
                        pass
                    remote_ws = None
                    continue
                        
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ 遠端轉發錯誤: {e}")
            try:
                if remote_ws:
                    remote_ws.close()
            except:
                pass
            remote_ws = None
            time.sleep(2)

# --- REST API Endpoints ---

@app.get("/api/status")
async def get_status():
    """取得系統狀態"""
    return {
        "plc_connected": plc is not None and plc.connection is not None,
        "remote_connected": remote_ws is not None,
        "sensor_status": latest_sensor_data['status'],
        "latest_data": latest_sensor_data,
        "active_websocket_connections": len(active_connections)
    }

@app.get("/health")
async def health():
    """健康檢查端點 (兼容舊版)"""
    return {"ok": True}

# --- PLC 控制端點 (關鍵功能) ---

@app.post("/on")
async def turn_on():
    """開啟 PLC 輸出 (寫入線圈 1280 = True)"""
    try:
        if plc is None or not plc.connection:
            return {"status": "error", "message": "PLC 未連線"}
        
        plc.open()  # 寫入線圈 1280 為 True
        print("🟢 PLC 輸出已開啟 (線圈 1280 = ON)")
        return {"status": "ok", "action": "on"}
            
    except Exception as e:
        print(f"❌ 開啟 PLC 輸出失敗: {e}")
        raise HTTPException(status_code=500, detail=f"操作失敗: {str(e)}")

@app.post("/off")
async def turn_off():
    """關閉 PLC 輸出 (寫入線圈 1280 = False)"""
    try:
        if plc is None or not plc.connection:
            return {"status": "error", "message": "PLC 未連線"}
        
        plc.close()  # 寫入線圈 1280 為 False (不會斷開連線)
        print("🔴 PLC 輸出已關閉 (線圈 1280 = OFF)")
        return {"status": "ok", "action": "off"}
            
    except Exception as e:
        print(f"❌ 關閉 PLC 輸出失敗: {e}")
        raise HTTPException(status_code=500, detail=f"操作失敗: {str(e)}")

# --- WebSocket Endpoint ---
@app.websocket("/ws/sensors")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint: 客戶端連上後可即時接收 PLC 資料"""
    await connect_client(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await disconnect_client(websocket)

# --- 啟動與關閉事件 ---
@app.on_event("startup")
async def startup_event():
    global main_loop
    print("=" * 60)
    print("🚀 啟動 AIoT 整合伺服器...")
    print("=" * 60)
    main_loop = asyncio.get_event_loop()
    
    init_plc()
    
    threading.Thread(target=data_collection_loop, daemon=True).start()
    print("✅ PLC 資料收集執行緒已啟動")
    
    threading.Thread(target=forward_to_remote, daemon=True).start()
    print("✅ 遠端轉發執行緒已啟動")
    
    print("-" * 60)
    print(f"🎉 本地 WebSocket: ws://{WS_HOST}:{WS_PORT}/ws/sensors")
    print(f"🌐 遠端轉發目標: {REMOTE_WS_URL}")
    print(f"🔧 PLC 控制: POST http://{WS_HOST}:{WS_PORT}/on or /off")
    print(f"📊 狀態查詢: GET http://{WS_HOST}:{WS_PORT}/api/status")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    global stop_thread, remote_ws
    print("=" * 60)
    print("🛑 關閉 AIoT 整合伺服器...")
    stop_thread = True
    
    if remote_ws:
        try:
            remote_ws.close()
            print("✅ 遠端 WebSocket 已關閉")
        except:
            pass
    
    # 注意:這裡不關閉 PLC 連線,保持設備狀態
    # 如果需要關閉連線,取消註解下面的程式碼
    # if plc and plc.connection:
    #     plc.disconnect()  # 或其他斷開連線的方法
    #     print("✅ PLC 連線已關閉")
    
    print("=" * 60)