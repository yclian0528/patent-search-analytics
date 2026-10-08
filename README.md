# 專利檢索分析網站

基於 Python 和 Streamlit 開發的台灣專利檢索分析網站。系統會在啟動時讀取 485 筆專利資料，提供條件檢索、專利瀏覽、單筆詳情，以及針對目前檢索結果產生統計分析。

## 背景

專利工程師的日常工作之一，是從大量專利中找出與特定技術或競爭對手相關的案件，再進一步分析技術布局。

本專案使用 485 筆台灣公告專利，包含發明、新型、設計三種類型，以及部分半導體領域（IPC H01L）的專利。資料來源為台灣智慧財產局公告資料。

## 功能

### 1. 專利檢索

- **關鍵字搜尋**：搜尋中文名稱、英文名稱、摘要與公告號。
- **專利類型**：可複選發明、新型及設計。
- **申請人**：從資料中動態產生中英文申請人選項，支援輸入文字快速尋找。
- **IPC 分類**：從全部 IPC 資料動態產生前四碼選項，支援複選。
- **公告日期區間**：以日曆選擇起日與迄日，邊界日期皆包含在檢索範圍內。

關鍵字請使用半形逗號 `,` 或全形逗號 `，` 分隔，因此包含空格的詞組仍可完整搜尋。例如：

```text
半導體封裝, 製造方法
```

輸入多個關鍵字時，搜尋結果需要同時符合所有關鍵字。同一項條件若選擇多個選項，符合其中一個即可；不同項目的條件則需要同時符合。

### 2. 專利瀏覽

- 以唯讀表格顯示符合條件的專利。
- 結果依公告日由新到舊排列。
- 可選取一筆結果，並在下方查看完整資料。
- 詳細資料包括公告號、證書號、申請號、專利類型、中英文名稱、申請人、發明人、日期、IPC、摘要及羅卡諾分類。

### 3. 統計分析

分析範圍會跟隨目前的檢索結果；未設定額外條件時，分析全部資料。

- **申請人排名**：列出前 10 名中文申請人及專利件數。共同申請案件會分別計入各申請人，同一案件不會重複計入同一申請人。
- **年度趨勢**：依公告年份統計專利件數。
- **IPC 分布**：統計前 10 名 IPC 前四碼。同一專利若有多個相同前綴，只計算一次；沒有 IPC 資料的專利不列入統計。

## 技術與執行環境

本專案基於 Python 3.11 做開發，以下為依賴套件

```text
altair==6.3.0
pandas==3.0.6
streamlit==1.65.0
```

程式使用 Python 3.10 以上版本才支援的型別語法，建議直接使用 Python 3.11 執行。

## 安裝與執行

以下指令請在專案根目錄執行。

### 1. 取得專案

```bash
git clone <repository-url>
cd patent-search-analytics
```

若已經取得專案壓縮檔，解壓縮後直接進入專案根目錄即可。

### 2. 建立虛擬環境

使用 Conda：

```bash
conda create -n patent-search python=3.11
conda activate patent-search
```

或使用 Python 內建的 `venv`：

```bash
python -m venv .venv
```

Windows PowerShell 啟用方式：

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS 或 Linux 啟用方式：

```bash
source .venv/bin/activate
```

### 3. 安裝依賴套件

```bash
python -m pip install -r requirements.txt
```

### 4. 啟動網站

```bash
python -m streamlit run app.py
```

啟動後，Streamlit 通常會自動開啟瀏覽器，也可以手動前往：

```text
http://localhost:8501
```

關閉瀏覽器分頁不會停止本機 Streamlit 服務。請回到執行指令的終端機按 `Ctrl+C` 結束服務。

## 操作方式

1. 在左側欄設定關鍵字、專利類型、申請人、IPC 與公告日期。
2. 按下「搜尋」，上方的符合件數、瀏覽結果及統計分析會同步更新。
3. 在「專利瀏覽」頁籤選取結果列，下方會顯示該筆專利的完整資料。
4. 切換至「統計分析」頁籤，選擇申請人排名、年度趨勢或 IPC 分布。

## 執行測試

請從專案根目錄執行：

```bash
python -m unittest discover -s tests -v
```

使用 `python -m unittest` 可以讓 Python 正確地將專案根目錄加入模組搜尋路徑。若直接執行 `python tests/test_data.py`，可能因執行位置不同而出現 `ModuleNotFoundError: No module named 'patents'`。

目前測試涵蓋：

- JSON 載入、欄位驗證、日期解析及動態 metadata。
- 文字正規化及關鍵字解析。
- 類型、申請人、IPC 與日期篩選規則。
- 申請人排名、年度趨勢與 IPC 分布的統計邏輯。
- Streamlit 頁面載入、搜尋結果、結果選取及分析方法切換。

## 專案結構

```text
patent-search-analytics/
├── app.py                    # Streamlit 畫面、互動流程與結果呈現
├── patents/
│   ├── __init__.py           # 將 patents 標示為 Python package
│   ├── data.py               # 載入、驗證、準備資料及建立篩選選項
│   ├── text.py               # 共用文字正規化規則
│   ├── search.py             # 查詢條件與專利篩選邏輯
│   └── analytics.py          # 申請人、年度及 IPC 統計邏輯
├── data/
│   └── raw/
│       └── patents.json      # 原始專利資料
├── tests/
│   ├── test_data.py          # 資料處理測試
│   ├── test_search.py        # 檢索規則測試
│   ├── test_analytics.py     # 分析邏輯測試
│   └── test_app.py           # Streamlit 介面流程測試
├── requirements.txt          # Python 套件版本
└── README.md                 # 專案說明
```

## 程式流程

```text
patents.json
     │
     ▼
patents/data.py ── 載入、驗證、建立正規化欄位與 metadata
     │
     ▼
app.py ── 取得使用者輸入並建立 SearchQuery
     │
     ▼
patents/search.py ── 篩選目前符合條件的專利
     │
     ├──► 專利列表與完整資料瀏覽
     │
     └──► patents/analytics.py ── 產生統計資料 ──► 表格或圖表
```

`app.py` 負責畫面與流程；資料讀取、檢索及統計邏輯分別放在獨立模組中，因此底層功能可以不依賴 Streamlit 單獨測試。

## 資料初始化與處理

網站啟動時會讀取完整 JSON 並存放於記憶體，同時動態整理：

- 原始欄位名稱與資料筆數。
- 專利類型選項。
- 中英文申請人選項。
- 所有 IPC 的前四碼選項。
- 申請日與公告日的最小、最大日期。

Streamlit 會快取初始化結果；當來源檔案的修改時間或大小改變時，資料會重新載入。

初始化階段會檢查必要欄位、公告號唯一性、陣列欄位型態、日期格式，以及申請日是否晚於公告日。系統會建立以下內部欄位供搜尋與分析使用：

- 經 Unicode NFKC、大小寫及空白處理的文字欄位。
- 可比較的日期欄位。
- 經標準化的申請人與 IPC 欄位。

原始欄位不會被覆寫，網站顯示與申請人排名仍使用來源資料中的文字。

如需在終端機檢查資料範圍與動態選項，可執行：

```bash
python -m patents.data
```

## 資料欄位

| 欄位 | 說明 | 範例 |
| --- | --- | --- |
| `patent_no` | 公告號（含類別碼） | `TWI915314B` |
| `certificate_no` | 證書號 | `I915314` |
| `application_no` | 申請號 | `109120607` |
| `type` | 專利類型：`invention` 發明、`model` 新型、`design` 設計 | `invention` |
| `title` / `title_en` | 專利名稱（中／英） | `具有各種焊球的球柵陣列（ＢＧＡ）封裝` |
| `abstract` | 摘要 | － |
| `applicants` / `applicants_en` | 申請人（中／英），可能有多個 | `["美商英特爾股份有限公司"]` |
| `inventors` | 發明人 | － |
| `application_date` | 申請日 | `2020-06-18` |
| `publication_date` | 公告日 | `2026-02-21` |
| `main_ipc` | 主要 IPC 分類 | `H01L023/488` |
| `ipc` | 所有 IPC 分類 | `["H01L023/488", "H01L023/498"]` |
| `locarno` | 羅卡諾分類（設計專利使用） | `["13-99"]` |

## 設計考量與目前限制

- 目前資料量為 485 筆，因此採用啟動時一次載入記憶體的方式，讓後續互動能立即使用已準備好的 DataFrame。
- 關鍵字搜尋目前採文字包含比對，沒有斷詞、同義詞擴展或相關性評分。
- 本專案是本機執行的 Streamlit 應用程式，沒有使用者帳號、資料庫或線上部署設定。
- 原始資料保留來源內容；正規化欄位只供比對，不會回寫 `patents.json`。