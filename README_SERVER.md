# AIoT 監控系統 PLC 本地端 Server (FastAPI)

## 概述
這是一個基於 **FastAPI** 的高效能本地端 HTTP API Server，用於提供 PLC 感測器資料的即時存取。

## 功能特色
- 🔄 即時感測器資料讀取
- 🌐 RESTful API 介面
- 💾 自動資料庫儲存
- 🔧 PLC 控制功能
- 📊 系統狀態監控
- 🔐 跨域請求支援 (CORS)
- ⚡ **FastAPI 高效能** - 基於 ASGI 的異步處理
- 📚 **自動 API 文檔** - Swagger UI & ReDoc
- 🛡️ **自動驗證** - Pydantic 模型驗證
- 🎯 **類型提示** - 完整的 Python 類型支援

## 安裝與設定

### 1. 安裝套件
```bash
pip install -r requirements.txt
```

主要套件：
- `fastapi` - 現代化 Web 框架
- `uvicorn` - ASGI 伺服器
- `pymodbus` - PLC 通訊
- `pymysql` - MySQL 資料庫

### 2. 設定 PLC 連線
在 `server.py` 中修改 PLC 連線設定：
```python
plc_info = {
    'framer': ModbusAsciiFramer,
    'port': "COM3",  # 修改為您的串列埠
    'stopbits': 1,
    'bytesize': 7,
    'parity': "E",
    'baudrate': 9600
}
```

### 3. 設定資料庫連線
執行資料庫設置工具：
```bash
python setup_database.py
```
或在 `components/db_connection.py` 中修改 MySQL 設定。

## 啟動伺服器

### 方法一：使用啟動腳本 (推薦)
```bash
python start_server.py
```

### 方法二：直接啟動
```bash
python server.py
```

### 方法三：使用 uvicorn 命令
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

伺服器將在以下位址啟動：
- **API 服務**: `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs` 📚
- **ReDoc**: `http://localhost:8000/redoc` 📖

## API 文檔

### 自動產生的文檔
FastAPI 會自動產生互動式 API 文檔：

1. **Swagger UI** (`/docs`) - 互動式 API 測試介面
2. **ReDoc** (`/redoc`) - 美觀的 API 文檔

### API 端點

#### 基本資訊
- **GET** `/` - 取得 API 資訊和端點列表

#### 感測器資料
- **GET** `/api/sensors/current` - 取得目前所有感測器資料
- **GET** `/api/sensors/temperature` - 取得溫度資料
- **GET** `/api/sensors/humidity` - 取得濕度資料
- **GET** `/api/sensors/air_quality` - 取得空氣品質資料 (PM2.5, PM10, CO2, TVOC)

#### PLC 控制
- **POST** `/api/plc/control` - 控制 PLC 輸出
  ```json
  {
    "action": "open"  // 或 "close"
  }
  ```

#### 系統狀態
- **GET** `/api/status` - 取得系統連線狀態

## API 回應格式

### 成功回應
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 錯誤回應
```json
{
  "success": false,
  "message": "錯誤描述",
  "error": "錯誤代碼"
}
```

## 使用範例

### 取得目前感測器資料
```bash
curl http://localhost:8000/api/sensors/current
```

### 控制 PLC 輸出
```bash
# 開啟輸出
curl -X POST -H "Content-Type: application/json" \
     -d '{"action":"open"}' \
     http://localhost:8000/api/plc/control

# 關閉輸出
curl -X POST -H "Content-Type: application/json" \
     -d '{"action":"close"}' \
     http://localhost:8000/api/plc/control
```

### 檢查系統狀態
```bash
curl http://localhost:8000/api/status
```

### 使用 Python requests
```python
import requests

# 取得感測器資料
response = requests.get('http://localhost:8000/api/sensors/current')
data = response.json()

# 控制 PLC
control_data = {"action": "open"}
response = requests.post('http://localhost:8000/api/plc/control', json=control_data)
```

## 感測器資料格式

```json
{
  "temperature": 25.5,     // 溫度 (°C)
  "humidity": 60.2,        // 濕度 (%)
  "pm25": 15,              // PM2.5 (μg/m³)
  "pm10": 20,              // PM10 (μg/m³)
  "pm25_average": 18,      // PM2.5 一小時平均
  "pm10_average": 22,      // PM10 一小時平均
  "co2": 400,              // CO2 (ppm)
  "tvoc": 0.5,             // TVOC (mg/m³)
  "timestamp": "2024-01-01T12:00:00.000000",
  "status": "connected"
}
```

## FastAPI vs Flask 主要變更

### 🔄 端口變更
- **舊版 (Flask)**: http://localhost:5000
- **新版 (FastAPI)**: http://localhost:8000

### 📚 新增功能
- **自動 API 文檔**: `/docs` 和 `/redoc`
- **資料驗證**: 使用 Pydantic 模型
- **更好的錯誤處理**: HTTP 狀態碼和結構化錯誤
- **類型提示**: 完整的 Python 類型支援
- **更高效能**: 基於 ASGI 的異步處理

### 🛠️ 開發體驗
- **更快的開發**: 自動補全和類型檢查
- **更好的測試**: 內建測試客戶端
- **更清晰的代碼**: Pydantic 模型和依賴注入

## 故障排除

### 常見問題

1. **伺服器無法啟動**
   - 檢查埠號 8000 是否被占用
   - 確認所有套件已正確安裝

2. **PLC 連線失敗**
   - 檢查串列埠設定是否正確
   - 確認 PLC 設備已連接並開啟

3. **資料庫連線失敗**
   - 執行 `python setup_database.py` 設置 SQLite
   - 檢查 MySQL 是否正在運行（如使用 MySQL）

4. **無法取得感測器資料**
   - 檢查 PLC 連線狀態
   - 查看伺服器終端輸出的錯誤訊息

5. **套件相容性問題**
   - 確認 Python 版本 >= 3.7
   - 重新安裝套件: `pip install -r requirements.txt --upgrade`

### 日誌監控
伺服器會在終端輸出詳細的運行日誌，包括：
- PLC 連線狀態
- 感測器資料讀取
- 資料庫操作結果
- HTTP 請求記錄 (uvicorn access log)

## 開發與自定義

### 新增 API 端點
在 `server.py` 中新增路由：
```python
@app.get("/api/custom/endpoint")
async def custom_endpoint():
    return {
        'success': True,
        'data': { ... },
        'message': '自定義端點'
    }
```

### 新增資料模型
使用 Pydantic 建立資料模型：
```python
from pydantic import BaseModel

class SensorData(BaseModel):
    temperature: float
    humidity: float
    timestamp: str
```

### 修改資料收集頻率
在 `data_collection_loop()` 函數中修改 `time.sleep(1)` 的數值。

### 開發模式啟動
```bash
uvicorn server:app --reload --port 8000
```

## 效能優化

### 生產環境設定
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

### 使用 Gunicorn (Linux/Mac)
```bash
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 安全注意事項
- 本伺服器設計用於本地網路環境
- 生產環境請考慮添加：
  - **身份驗證**: JWT 或 API Key
  - **HTTPS**: SSL/TLS 加密
  - **限制 CORS**: 指定允許的來源
  - **API 限速**: 防止濫用
- 定期更新套件以確保安全性

## 技術支援
如有問題，請檢查：
1. **Swagger UI**: http://localhost:8000/docs - 測試 API
2. 系統日誌輸出
3. PLC 連線狀態
4. 資料庫連線狀態
5. 網路設定

## 版本歷史
- **v2.0.0**: 升級到 FastAPI，新增自動文檔和更好的效能
- **v1.0.0**: 原始 Flask 版本 