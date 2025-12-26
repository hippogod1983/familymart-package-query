# 全家便利商店包裹查詢程式

自動查詢全家便利商店 (FamilyMart) 包裹物流狀態的 Python 程式。

## 功能特色

- ✅ 自動辨識驗證碼（使用 ddddocr）
- ✅ 支援複數包裹同時查詢
- ✅ 驗證碼辨識失敗自動重試
- ✅ 查詢結果清楚顯示

## 安裝步驟

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定包裹編號

編輯 `config.yaml` 檔案，填入要查詢的包裹編號：

```yaml
tracking_numbers:
  - "你的包裹編號1"
  - "你的包裹編號2"
  - "你的包裹編號3"

max_retries: 5
```

## 使用方式

```bash
python query_package.py
```

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
| `max_retries` | 驗證碼辨識失敗時的最大重試次數 | 5 |
| `output_file` | 查詢結果輸出檔案路徑 | `result.txt` |

## 注意事項

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
