# CLAUDE.md

此檔案為 Claude Code (claude.ai/code) 在此儲存庫中工作時提供指引。

## 專案概述

**SunnetChat** 是一個具備先進 RAG（檢索增強生成）功能的智慧 AI Slack 聊天機器人。系統提供：

- 使用向量相似度從內部知識庫進行智慧文件搜尋
- 當內部文件不包含答案時自動回退到網路搜尋
- 自動將新知識儲存到 Google Drive 以實現知識持久化
- 基於 FastAPI 構建的即時非同步處理
- 具備適當身份驗證的企業級安全性

此程式碼庫採用雙語設計，文件使用繁體中文（zh-TW），程式碼使用英文。

## 技術堆疊

**核心框架**：Python 3.11+ 搭配 FastAPI（非同步網頁框架）和 Uvicorn（ASGI 伺服器）

**AI/ML 堆疊**：
- LangChain：RAG 框架和編排
- LangGraph：狀態化、多角色應用程式工作流程
- Ollama：本地 LLM 推理（預設：llama3 模型）
- Google Generative AI：嵌入模型（models/embedding-001）
- ChromaDB：語意搜尋向量資料庫
- Tavily：網路搜尋整合

**整合**：Slack Bolt（非同步）、Google Drive API

**測試**：pytest 搭配非同步支援、pytest-cov、httpx

**程式碼品質**：flake8（最大行長度 127、複雜度 ≤10）、black 格式化工具

## 開發指令

### 設定

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows：venv\Scripts\activate

# 安裝相依套件
pip install -r requirements.txt

# 配置環境
cp .env.example .env
# 編輯 .env 填入您的憑證
```

### 執行應用程式

**Docker（建議）**：
```bash
docker-compose up -d              # 啟動所有服務
docker-compose ps                 # 檢查狀態（尋找 "healthy" 狀態）
docker inspect --format='{{.State.Health.Status}}' slack_agent_app  # 驗證健康狀態
docker-compose logs -f app        # 查看日誌
docker-compose down               # 停止服務
docker-compose down -v            # 停止並移除卷
```

**本地開發**：
```bash
docker-compose up chromadb ollama -d  # 僅啟動相依服務
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 測試

```bash
pytest                                    # 執行所有測試
pytest --cov=app --cov-report=html       # 包含覆蓋率報告
pytest tests/test_api.py -v              # 特定測試檔案
pytest tests/test_slack_integration.py -v # 整合測試
```

### 程式碼品質

```bash
black app/ tests/                 # 格式化程式碼
flake8 app/ tests/                # 程式碼檢查
```

### 文件管理

```bash
python scripts/ingest.py          # 將文件匯入向量資料庫
```

### Ollama 模型管理

```bash
docker exec -it ollama ollama pull llama3   # 下載模型
docker exec -it ollama ollama list          # 列出可用模型
```

## 架構

### 使用 LangGraph 工作流程的代理式 RAG

系統使用**混合檢索生成模式**搭配智慧路由：

```
使用者問題（Slack）
    ↓
FastAPI Webhook 處理器（main.py）
    ↓
CoreAgent - LangGraph 狀態機（core_agent.py）
    ↓
[1] retrieve → [2] grade_documents
    ↓
    ├─→ [3a] generate_from_docs（若找到相關文件）
    │   或
    ├─→ [3b] web_search → generate_from_web → [4] save_knowledge
    ↓
回應使用者（Slack 執行緒）
```

**關鍵設計決策**：
- 在生成前對文件進行相關性評分（減少幻覺）
- 僅當本地文件評分不相關時才觸發網路搜尋
- 網路搜尋的知識自動儲存到 Google Drive
- 背景任務處理避免 Slack 3 秒逾時
- 具有指數退避的綜合重試機制

### 核心元件

#### `app/core_agent.py` - 主要實作

系統核心包含：
- **CoreAgent 類別**：使用單例模式管理整個 RAG 工作流程
- **LangGraph 狀態機**：具有條件路由的 6 節點工作流程
- **TaskStatus 追蹤**：PENDING → RUNNING → COMPLETED/FAILED/RETRYING
- **多語言提示詞**：支援 zh-TW 和英文
- **非同步優先設計**：所有操作均為非同步相容

透過 `get_agent()` 函式存取以確保請求間的單一實例。

#### `app/main.py` - FastAPI 進入點

- 單一健康檢查端點（`/health`）
- `app_mention` 事件的 Slack webhook 處理
- **關鍵模式**：使用 `asyncio.create_task()` 進行背景處理
- 記憶體內的活動任務追蹤字典
- 立即確認 → 背景處理 → 執行緒回應

#### `app/vector_store.py` - 向量資料庫操作

- **ChromaDB 整合**：嘗試 HTTP 客戶端（Docker）→ 回退到本地目錄
- **文字分塊**：RecursiveCharacterTextSplitter（大小=1000、重疊=200）
- **嵌入**：Google 的 embedding-001 模型
- **預設集合**："internal_sop"
- **檢索**：Top-k=3 個文件

#### `app/data_processor.py` - 文件處理

- **支援格式**：.txt、.pdf、.docx、.pptx、.xlsx、圖片（JPG/PNG/GIF）
- **OCR**：Tesseract 搭配繁體中文支援（chi-tra）
- 使用 UnstructuredFileLoader 實現廣泛的格式相容性

#### `app/agent.py` - 向後相容性

包裝 `core_agent.py` 以維持舊介面，同時使用新實作。

### 服務架構（Docker Compose）

**容器基礎設施** - 生產就緒的多階段設定：

#### 1. **app**（FastAPI 應用程式）

- **埠號**：8000（可透過 `PORT` 環境變數配置）
- **使用者**：非 root 的 `appuser`（UID 1000）以增強安全性
- **Worker 數量**：4 個 Uvicorn worker 進程（可透過 `WORKERS` 環境變數配置）
- **構建策略**：多階段 Docker 構建（構建器 + 執行時階段）
  - 構建器階段：使用構建工具編譯相依套件
  - 執行時階段：僅包含執行時相依的乾淨環境
  - 結果：映像檔大小減少 30-40%
- **健康檢查**：Docker 健康檢查自動監控
  - 間隔：每 30 秒
  - 逾時：10 秒
  - 啟動期：40 秒（允許初始化）
  - 重試：標記為不健康前連續失敗 3 次
  - 端點：`GET /`（回傳健康狀態）
- **系統相依**：
  - `tesseract-ocr` + `tesseract-ocr-chi-tra`：支援繁體中文的 OCR
  - `libmagic1`：檔案類型偵測（unstructured 套件所需）
  - `poppler-utils`：PDF 處理和轉換
  - `pandoc`：DOCX/PPTX 文件轉換
  - `curl`：健康檢查工具
- **卷**：`/app/local_documents` 用於文件持久化
- **構建優化**：`.dockerignore` 排除不必要的檔案（tests、git、venv 等）

#### 2. **ollama**（LLM 推理服務）

- **埠號**：11434
- **預設模型**：llama3（首次執行必須手動拉取）
- **卷**：`ollama_data` 用於模型持久化
- **用途**：本地 LLM 推理用於生成和文件評分

#### 3. **chromadb**（向量資料庫服務）

- **埠號**：8001（容器內部埠 8000，對映以避免與 FastAPI 衝突）
- **卷**：`chroma_data` 用於資料庫持久化
- **集合**：`internal_sop`（預設）
- **用途**：文件檢索的向量相似度搜尋

**架構優勢**：
- 隔離的服務便於擴展
- 持久化卷用於資料保留
- 健康監控實現自動恢復
- 非 root 執行符合安全規範

## Docker 安全與優化

### 多階段構建架構

Dockerfile 實作了複雜的兩階段構建模式以優化映像檔大小和安全性：

**階段 1：構建器**
```dockerfile
FROM python:3.11-slim as builder
```
- 安裝編譯工具（gcc、g++、python3-dev）
- 編譯所有 Python 相依套件
- 將套件儲存在使用者目錄（`/root/.local`）
- 此階段在構建後被捨棄

**階段 2：執行時**
```dockerfile
FROM python:3.11-slim
```
- 從乾淨的 Python 基礎映像開始
- 僅從構建器階段複製編譯後的套件
- 安裝最小的執行時系統相依
- 最終映像不包含構建工具

**優勢**：
- **映像大小**：相較於單階段構建減少 30-40%
- **安全性**：生產映像中沒有編譯工具，減少攻擊面
- **構建速度**：層快取優化重建時間

### 安全最佳實踐

**非 Root 使用者執行**：
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```
- 應用程式以專用的 `appuser`（UID 1000）執行
- 防止權限提升攻擊
- 遵循最小權限原則
- 容器無法修改系統檔案

**構建上下文優化**：
- `.dockerignore` 檔案排除：
  - 原始碼管理檔案（`.git/`、`.github/`）
  - 測試檔案（`tests/`、`.pytest_cache/`）
  - Python 快取（`__pycache__/`、`*.pyc`）
  - 虛擬環境（`venv/`、`.venv/`）
  - 開發配置（`.vscode/`、`.idea/`）
  - 敏感檔案（`*.env` 除了 `.env.example`）
- 減少約 70-80% 的構建上下文大小
- 防止意外包含機密資訊
- 加速 Docker 構建流程

**容器元數據**（OCI 標籤）：
```dockerfile
LABEL maintainer="SunnetChat Team"
LABEL version="1.0.0"
LABEL description="SunnetChat - Intelligent AI Slack Bot with RAG capabilities"
LABEL org.opencontainers.image.source="https://github.com/trionnemesis/sunnetchat"
```
- 啟用版本追蹤
- 連結到原始碼儲存庫
- 便於自動化工具

### 健康檢查系統

**配置**：
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1
```

**參數說明**：
- `--interval=30s`：正常運作期間每 30 秒檢查一次
- `--timeout=10s`：健康檢查指令必須在 10 秒內完成
- `--start-period=40s`：應用程式初始化的寬限期（不計算失敗）
- `--retries=3`：連續失敗 3 次後標記為不健康
- **端點**：`GET /`（主健康檢查端點）

**健康狀態**：
- `starting`：啟動期間的初始狀態（前 40 秒）
- `healthy`：應用程式正常回應
- `unhealthy`：連續 3 次健康檢查失敗

**排障指令**：
```bash
# 檢查目前健康狀態
docker inspect --format='{{.State.Health.Status}}' slack_agent_app

# 查看詳細健康檢查日誌
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' slack_agent_app

# 手動健康檢查測試
curl http://localhost:8000/

# 即時監控健康狀態
watch -n 5 'docker inspect --format="{{.State.Health.Status}}" slack_agent_app'
```

**常見健康檢查問題**：
- **啟動延遲**：應用程式可能需要 30-40 秒初始化（正常）
- **埠衝突**：驗證埠 8000 未被其他服務使用
- **相依失敗**：檢查 ChromaDB 和 Ollama 服務是否健康
- **環境問題**：驗證所有必要的環境變數已設定

### 效能優化

**層快取策略**：
Dockerfile 排序以最大化 Docker 的層快取：
1. 系統相依（很少變更）→ 快取最久
2. Python 套件需求（偶爾變更）→ 中度快取
3. 應用程式程式碼（頻繁變更）→ 經常重建

**多 Worker 配置**：
```dockerfile
ENV WORKERS=4
```
- 預設：生產環境 4 個 worker 進程
- 建議：CPU 密集型工作負載使用 2-4× CPU 核心數
- 透過 `WORKERS` 環境變數調整
- 每個 worker 獨立處理請求

**卷宣告**：
```dockerfile
VOLUME ["/app/local_documents"]
```
- 明確宣告持久化資料位置
- 讓 Docker 優化儲存驅動程式
- 便於備份和遷移策略

## 關鍵技術見解

### 單例代理模式

`get_agent()` 確保請求間的單一 CoreAgent 實例以避免重新初始化開銷。代理管理：
- LangGraph 工作流程編譯
- LLM 和嵌入模型初始化
- 向量存儲連接
- 配置狀態

### 雙路徑生成策略

- **路徑 A（本地）**：retrieve → grade → generate（快速、私有知識）
- **路徑 B（網路）**：retrieve → grade → web_search → generate → save to Drive（較慢、外部）

系統根據 LLM 評分的文件相關性分數智慧路由。

### 非同步背景處理

對於 Slack 整合至關重要：
1. Webhook 接收請求
2. 立即向 Slack 回應 200 OK
3. `asyncio.create_task()` 在背景處理
4. 完成時將結果發布到執行緒

這可防止 Slack 的 3 秒逾時，同時允許 10-30 秒的 LLM 處理。

### 重試機制

`_retry_with_backoff()` 保護所有外部 API 呼叫：
- 可配置的 MAX_RETRIES（預設：3）
- 指數退避：2^嘗試 秒
- 應用於：LLM 呼叫、嵌入、向量搜尋、網路搜尋、Drive 上傳

### ChromaDB 連接處理

程式碼首先嘗試 HTTP 客戶端（用於 Docker 環境），然後優雅地回退到本地目錄模式（用於開發）。如果看到連接問題請檢查日誌。

### 文件評分流程

在從檢索到的文件生成之前，LLM 會評分其相關性：
- 分數："yes"（相關）或 "no"（不相關）
- 多個文件 → 篩選到相關子集
- 無相關文件 → 觸發網路搜尋路徑
- 透過避免不相關上下文顯著減少幻覺

## 測試慣例

- **框架**：pytest 搭配 `asyncio_mode = auto`（pytest.ini）
- **模擬**：在 `conftest.py` 中大量使用以防止實際的 Slack API 呼叫
- **固定裝置**：集中式模擬客戶端（Slack、LLM、向量存儲）
- **覆蓋率**：使用 pytest-cov 追蹤，在 CI 中上傳到 Codecov
- **命名**：標準 pytest 慣例（`test_*.py`、`Test*`、`test_*`）

## CI/CD 流水線

GitHub Actions 包含 3 個平行任務：

1. **測試與檢查**（ubuntu-latest、Python 3.11）
   - ChromaDB 服務容器
   - Tesseract OCR 安裝
   - flake8（錯誤 + 複雜度檢查）
   - black 格式驗證
   - pytest 搭配覆蓋率 → Codecov

2. **構建**（依賴測試通過）
   - Docker Buildx 多平台
   - 使用 commit SHA + latest 標記
   - 冒煙測試（curl 健康端點）

3. **安全掃描**（獨立）
   - Trivy 檔案系統掃描
   - SARIF 上傳到 GitHub Security

**觸發條件**：推送到 master/develop、對 master 的 PR、手動調度

## 配置

所有配置透過環境變數（`.env` 檔案）：

**必要**：
- `SLACK_BOT_TOKEN`：Slack 機器人 OAuth token
- `SLACK_SIGNING_SECRET`：Webhook 驗證
- `GOOGLE_API_KEY`：用於嵌入
- `TAVILY_API_KEY`：用於網路搜尋
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`：服務帳戶 JSON（作為字串，非檔案路徑）

**選用**（有預設值）：
- `OLLAMA_BASE_URL`：LLM 端點（預設：http://localhost:11434）
- `CHROMA_HTTP_HOST`：向量資料庫主機（預設：localhost）
- `CHROMA_HTTP_PORT`：向量資料庫埠（預設：8001）
- `LLM_MODEL`：Ollama 模型名稱（預設：llama3）
- `MAX_RETRIES`：重試次數（預設：3）
- `LANGUAGE`：提示詞語言（預設：zh-TW）
- `PORT`：應用程式監聽埠（預設：8000）
- `WORKERS`：Uvicorn worker 進程數量（預設：4）
- `LOG_LEVEL`：應用程式日誌級別 - debug/info/warning/error（預設：info）

## 常見問題

1. **Ollama 模型**：首次使用前必須透過 `docker exec -it ollama ollama pull llama3` 手動拉取 llama3
2. **Tesseract**：OCR 需要系統套件（apt-get install tesseract-ocr tesseract-ocr-chi-tra）
3. **Google 憑證**：以 JSON 字串形式傳遞到環境變數，非檔案路徑
4. **首次執行**：冷啟動需要 5-10 秒（模型載入、服務連接）
5. **效能**：完整工作流程通常需要 10-30 秒（檢索 1-2 秒、LLM 3-10 秒、網路搜尋 2-5 秒）
6. **健康檢查**：容器啟動期間初始 `starting` 狀態持續 30-40 秒是正常的；等待 `healthy` 狀態再認為服務就緒
7. **Docker 構建快取**：如果遇到過時相依問題，使用 `--no-cache` 旗標重建：`docker-compose build --no-cache`
8. **Worker 數量**：根據可用 CPU 核心調整 `WORKERS` 環境變數（建議：2-4× CPU 數量以達最佳效能）
9. **容器權限**：掛載的卷必須可由 UID 1000（appuser）讀寫；如果發生權限錯誤使用 `chown -R 1000:1000 /path/to/volume`

## 生產環境部署

### Docker 生產設定

**基本部署**：
```bash
# 以生產模式啟動所有服務
docker-compose up -d

# 驗證所有容器都健康
docker-compose ps
# 在輸出中尋找 "healthy" 狀態

# 監控日誌
docker-compose logs -f app
```

**進階配置**：
```bash
# 使用自訂 worker 數量和日誌級別執行
docker run -d \
  --name sunnetchat \
  -p 8000:8000 \
  --env-file .env.prod \
  -e PORT=8000 \
  -e WORKERS=8 \
  -e LOG_LEVEL=warning \
  -v /path/to/docs:/app/local_documents \
  --user 1000:1000 \
  --restart unless-stopped \
  --health-cmd="curl -f http://localhost:8000/ || exit 1" \
  --health-interval=30s \
  --health-timeout=10s \
  --health-retries=3 \
  sunnetchat:latest
```

**健康狀態監控**：
```bash
# 檢查健康狀態
docker inspect --format='{{.State.Health.Status}}' slack_agent_app

# 自動化監控腳本
watch -n 10 'docker inspect --format="Health: {{.State.Health.Status}}" slack_agent_app'

# 查看健康檢查歷史記錄
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' slack_agent_app
```

### 效能調校

**Worker 配置**：
- **低流量**（< 10 請求/分鐘）：`WORKERS=2`
- **中流量**（10-50 請求/分鐘）：`WORKERS=4`（預設）
- **高流量**（50-200 請求/分鐘）：`WORKERS=8`
- **超高流量**（> 200 請求/分鐘）：`WORKERS=16` + 考慮水平擴展

**資源配置**：
- **最低需求**：
  - 2GB RAM
  - 2 CPU 核心
  - 10GB 儲存空間
- **生產環境建議**：
  - 4GB RAM
  - 4 CPU 核心
  - 20GB 儲存空間
- **高效能設定**：
  - 8GB+ RAM
  - 8+ CPU 核心
  - 50GB+ 儲存空間

### 生產環境安全檢查清單

部署到生產環境前，請驗證：

- [ ] 容器以非 root 使用者執行（UID 1000 - appuser）
- [ ] 所有敏感環境變數在 `.env` 檔案中（未提交到 git）
- [ ] `.dockerignore` 正確配置
- [ ] 健康檢查已啟用且通過
- [ ] 已配置資源限制（`--memory`、`--cpus`）
- [ ] 已設定重啟策略（`--restart unless-stopped`）
- [ ] 卷具有正確權限（UID 1000）
- [ ] 已配置防火牆規則（僅允許必要埠）
- [ ] 已排程定期安全掃描（Trivy 在 CI/CD 中執行）
- [ ] 已配置日誌聚合
- [ ] 持久化卷的備份策略

### 生產問題排除

**容器無法啟動**：
```bash
# 檢查詳細日誌
docker logs slack_agent_app --tail 100

# 驗證環境變數
docker exec slack_agent_app env | grep -E "SLACK|GOOGLE|TAVILY"

# 測試相依服務
docker-compose ps  # 確保 ollama 和 chromadb 正在執行
```

**健康檢查失敗**：
```bash
# 手動健康檢查測試
curl -v http://localhost:8000/

# 檢查埠是否可訪問
netstat -an | grep 8000

# 使用乾淨狀態重啟
docker-compose down -v
docker-compose up -d
```

**效能問題**：
```bash
# 監控資源使用
docker stats slack_agent_app

# 增加 worker 數量
docker-compose down
# 編輯 .env：WORKERS=8
docker-compose up -d

# 檢查記憶體洩漏
docker exec slack_agent_app ps aux
```

## Git 工作流程

- **主分支**：`master`
- **開發分支**：`develop`
- **提交風格**：傳統式提交（例如：`feat:`、`fix:`、`docs:`）
- **PR 目標**：master 分支
