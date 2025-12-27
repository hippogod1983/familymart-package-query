# 全家便利商店包裹查詢程式

> **版本: 0.03**

自動查詢全家便利商店 (FamilyMart) 包裹物流狀態的 Python 程式。

## 功能特色

### 核心功能
- ✅ 自動辨識驗證碼（使用 ddddocr）
- ✅ 支援複數包裹同時查詢
- ✅ 驗證碼辨識失敗自動重試
- ✅ 查詢結果清楚顯示

### GUI 增強功能 (v0.03 新增)
- 📋 剪貼簿一鍵貼上
- 🔧 右鍵選單（複製/重新查詢/刪除）
- 🔍 狀態篩選和快速搜尋
- 📂 拖放 TXT 檔案載入包裹編號
- 📜 歷史記錄頁籤
- 📥 匯出 Excel/CSV
- ⚙️ 設定頁面
- 🌙 深色/淺色主題切換
- 🌐 多語系支援（繁中/簡中/英文）
- ⏰ 自動定時查詢
- 📌 視窗大小位置記憶

## 安裝步驟

### 1. 建立虛擬環境 (使用 uv)

```bash
uv venv --python 3.11
```

### 2. 安裝依賴套件

```bash
uv add requests beautifulsoup4 ddddocr pyyaml
```

或使用 pip：

```bash
pip install -r requirements.txt
```

### 3. 設定包裹編號

複製設定檔範例並編輯：

```bash
cp config.yaml.example config.yaml
```

編輯 `config.yaml` 檔案，填入要查詢的包裹編號：

```yaml
tracking_numbers:
  - "你的包裹編號1"
  - "你的包裹編號2"
  - "你的包裹編號3"

max_retries: 3
```

## 使用方式

### 圖形介面版本（推薦）

```bash
uv run gui_app.py
```

啟動視窗化應用程式，直接在視窗中輸入包裹編號進行查詢。

**功能特色：**
- 📦 直接在視窗輸入包裹編號（每行一個）
- 🔍 一鍵查詢，即時顯示結果
- 📋 支援複製查詢結果
- ⏳ 背景執行，介面不會凍結

### 命令列版本

```bash
uv run query_package.py
```

**命令列參數：**

| 參數 | 說明 |
|------|------|
| `-r` | 產生 requirements.txt 檔案 |
| `-c` | 清除產生的檔案 (result.txt, debug_result.json) |
| `-v` | 顯示版本資訊 |

程式會自動：
1. 載入設定檔中的包裹編號
2. 連接全家查詢網站
3. 下載並辨識驗證碼
4. 提交查詢並取得結果
5. 顯示包裹最新狀態

## 設定說明

| 參數 | 說明 | 預設值 |
|------|------|--------|
| `tracking_numbers` | 要查詢的包裹編號列表 | 空 |
| `max_retries` | 驗證碼辨識失敗時的最大重試次數 | 3 |
| `output_file` | 查詢結果輸出檔案路徑 | `result.txt` |

## 注意事項

- ⚠️ **需要 Python 3.11** (ddddocr 不支援 Python 3.14+)
- 每次最多可同時查詢 5 個包裹編號
- 若包裹數量超過 5 個，程式會自動分批查詢
- 驗證碼辨識可能偶爾失敗，程式會自動重試

## 依賴套件

- `requests` - HTTP 請求
- `beautifulsoup4` - HTML 解析
- `ddddocr` - 驗證碼辨識
- `pyyaml` - YAML 設定檔解析

## 授權

MIT License
