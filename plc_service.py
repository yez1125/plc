from fastapi import FastAPI
from components.plc_connection import PLCConnection
from pymodbus.transaction import ModbusAsciiFramer

# === PLC 基本設定 ===
plc_info = {
    "framer": ModbusAsciiFramer,
    "port": "COM3",
    "stopbits": 1,
    "bytesize": 7,
    "parity": "E",
    "baudrate": 9600
}

plc = PLCConnection(**plc_info)
plc.connect()

app = FastAPI(title="PLC Switch API")

@app.post("/on")
def turn_on():
    plc.open()
    return {"status": "ok", "action": "on"}

@app.post("/off")
def turn_off():
    plc.close()
    return {"status": "ok", "action": "off"}

@app.get("/health")
def health():
    return {"ok": True}
