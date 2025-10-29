# SunnetChat 智慧聊天機器人 🤖💬

[![CI/CD 流水線](https://github.com/trionnemesis/sunnetchat/actions/workflows/ci.yml/badge.svg)](https://github.com/trionnemesis/sunnetchat/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com)
[![授權條款: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 一個具備先進 RAG（檢索增強生成）功能的智慧 AI Slack 聊天機器人，專為文件處理、知識管理和即時資訊檢索而設計。

## 🌟 主要功能

### 核心能力
- **🔍 智慧文件搜尋**：使用向量相似度搜尋從您的內部知識庫中檢索相關資訊
- **🌐 網路搜尋整合**：當內部文件不包含答案時，自動回退到即時網路搜尋
- **📚 知識儲存**：自動將新知識儲存到 Google Drive 以供未來參考
- **⚡ 即時處理**：基於 FastAPI 構建，支援高效能非同步操作
- **🔒 企業級安全**：具備適當身份驗證的安全 Slack 整合

### RAG 流水線
- **向量嵌入**：使用 Google 的 `embedding-001` 模型進行語意理解
- **文件評分**：智慧相關性評分以確定最佳資訊來源
- **多模態搜尋**：支援文字、圖片、PDF、DOCX、PPTX 等多種格式
- **對話流程**：由 LangGraph 驅動的對話管理

### 部署與擴展
- **🐳 Docker 就緒**：使用 Docker Compose 完整容器化
- **🚀 生產就緒**：針對部署進行最佳化，包含健康檢查和監控
- **🔄 CI/CD 流水線**：全面的測試、安全掃描和自動化部署
- **📊 可觀測性**：內建日誌記錄和錯誤處理

### Docker 優化特性
- **🏗️ 多階段構建**：分離構建和運行環境，減少映像檔體積約 30-40%
- **🔒 非 root 用戶**：使用專用 appuser (UID 1000) 運行，增強容器安全性
- **❤️ 健康檢查**：每 30 秒自動監控應用程式運行狀態，支援自動重啟
- **📦 智慧快取**：.dockerignore 優化構建效率，排除不必要的檔案
- **📚 豐富依賴**：完整支援 OCR（中文繁體）、PDF、DOCX/PPTX 文件處理
- **⚡ 多 Worker**：預設 4 個 worker 進程，提升並發處理能力

## 🏗️ 系統架構

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Slack User    │───▶│   FastAPI App   │───▶│   LangGraph     │
└─────────────────┘    └─────────────────┘    │   Agent         │
                                              └─────────────────┘
                                                       │
                       ┌────────────────────────────────┼────────────────────────────────┐
                       │                                │                                │
                       ▼                                ▼                                ▼
           ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
           │   ChromaDB      │              │   Ollama        │              │   Tavily        │
           │   (Vector DB)   │              │   (LLM)         │              │   (Web Search)  │
           └─────────────────┘              └─────────────────┘              └─────────────────┘
                       │                                                               │
                       ▼                                                               ▼
           ┌─────────────────┐                                              ┌─────────────────┐
           │   Google Drive  │                                              │   Google        │
           │   (Knowledge    │                                              │   Embeddings    │
           │    Storage)     │                                              │                 │
           └─────────────────┘                                              └─────────────────┘
```

## 🚀 快速開始

### 前置需求

- Docker 和 Docker Compose
- Python 3.11+
- 具有 Bot Token 的 Slack 應用程式
- Google API 憑證（用於 Drive 和嵌入模型）
- Tavily API 金鑰（用於網路搜尋）

### 1. 複製專案並設定

```bash
git clone https://github.com/trionnemesis/sunnetchat.git
cd sunnetchat
cp .env.example .env
```

### 2. 設定環境變數

編輯 `.env` 檔案並填入您的憑證：

```bash
# Slack 設定
SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
SLACK_SIGNING_SECRET="your-slack-signing-secret-here"

# Google 服務
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_DRIVE_FOLDER_ID="your-google-drive-folder-id"
GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type": "service_account", ...}'

# Tavily 網路搜尋
TAVILY_API_KEY="tvly-your-tavily-api-key"

# 本地知識庫
LOCAL_KNOWLEDGE_BASE_PATH="/path/to/your/documents"
```

### 3. 使用 Docker 啟動

```bash
# 首次啟動前，請確認 docker-compose.yml 中的卷掛載路徑
# 預設掛載：C:\SUNNET:/app/local_documents
# 請根據您的系統修改為適合的路徑（Windows/Linux/macOS）

# 啟動所有服務
docker-compose up -d

# 檢查狀態（確認健康檢查通過）
docker-compose ps

# 查看日誌
docker-compose logs -f app

# 驗證應用程式是否正常運行
curl http://localhost:8000/
# 預期回應：{"status":"ok"} 或類似的健康檢查回應
```

**提示**：健康檢查可能需要 30-40 秒才會顯示為 "healthy" 狀態，這是正常的啟動時間。

### 4. 設定 Slack 整合

1. 在 [api.slack.com](https://api.slack.com/apps) 建立 Slack 應用程式
2. 啟用事件訂閱：`http://your-domain.com/slack/events`
3. 訂閱 `app_mention` 事件
4. 將應用程式安裝到工作區
5. 邀請機器人加入頻道：`/invite @YourBot`

## 🧪 開發指南

### 本地開發環境設定

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows 系統：venv\Scripts\activate

# 安裝相依套件
pip install -r requirements.txt

# 分別啟動服務
docker-compose up chromadb ollama -d

# 本地執行應用程式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 執行測試

```bash
# 執行所有測試
pytest

# 執行測試並產生覆蓋率報告
pytest --cov=app --cov-report=html

# 執行特定測試檔案
pytest tests/test_api.py -v

# 執行整合測試
pytest tests/test_slack_integration.py -v
```

### 程式碼品質檢查

```bash
# 格式化程式碼
black app/ tests/

# 程式碼檢查
flake8 app/ tests/

# 型別檢查（如果使用 mypy）
mypy app/
```

## 📁 專案結構

```
sunnetchat/
├── 📁 app/                     # Main application code
│   ├── 🐍 main.py             # FastAPI application & Slack handlers
│   ├── 🧠 agent.py            # LangGraph agent with RAG pipeline
│   ├── 🏭 factory.py          # Application factory patterns
│   ├── ⚙️ rag_core.py         # Core RAG functionality
│   ├── 📊 vector_store.py     # Vector database operations
│   ├── 🔄 data_processor.py   # Document processing utilities
│   ├── 📁 gdrive_utils.py     # Google Drive integration
│   └── 🌊 graph_flow.py       # LangGraph workflow definitions
├── 🧪 tests/                  # Comprehensive test suite
│   ├── 🧪 test_api.py         # API endpoint tests
│   ├── 🧪 test_rag_core.py    # RAG pipeline tests
│   ├── 🧪 test_slack_integration.py  # Slack integration tests
│   ├── 🧪 test_vector_store.py      # Vector database tests
│   └── 🧪 conftest.py         # Test configuration & fixtures
├── 📁 scripts/               # Utility scripts
│   └── 🐍 ingest.py          # Document ingestion script
├── 🔧 .github/workflows/     # CI/CD pipeline
│   └── ⚙️ ci.yml             # GitHub Actions configuration
├── 🐳 docker-compose.yml     # Multi-container setup
├── 🐳 Dockerfile            # Application container (multi-stage build)
├── 🚫 .dockerignore         # Docker build optimization
├── 📋 requirements.txt       # Python dependencies
└── 📖 README.md             # This file
```

## 🔧 設定配置

### 環境變數

| 變數名稱 | 描述 | 必要性 | 預設值 |
|----------|-------------|----------|---------|
| `SLACK_BOT_TOKEN` | Slack 機器人的 OAuth Token | ✅ | - |
| `SLACK_SIGNING_SECRET` | Slack 應用程式簽名秘鑰 | ✅ | - |
| `GOOGLE_API_KEY` | Google 嵌入模型的 API 金鑰 | ✅ | - |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive 儲存資料夾 ID | ✅ | - |
| `TAVILY_API_KEY` | Tavily 網路搜尋的 API 金鑰 | ✅ | - |
| `LOCAL_KNOWLEDGE_BASE_PATH` | 本地文件路徑 | ❌ | `/app/local_documents` |
| `CHROMA_HOST` | ChromaDB 主機位址 | ❌ | `chromadb` |
| `CHROMA_PORT` | ChromaDB 連接埠 | ❌ | `8000` |
| `OLLAMA_BASE_URL` | Ollama 服務 URL | ❌ | `http://ollama:11434` |
| `LLM_MODEL` | Ollama 模型名稱 | ❌ | `llama3` |
| `PORT` | 應用程式監聽埠 | ❌ | `8000` |
| `WORKERS` | Uvicorn worker 進程數量 | ❌ | `4` |
| `LOG_LEVEL` | 日誌級別（debug/info/warning/error） | ❌ | `info` |

### Docker 服務

- **app**：主要的 FastAPI 應用程式
  - **連接埠**：8000（可透過 `PORT` 環境變數配置）
  - **執行用戶**：appuser (UID 1000，非 root 用戶)
  - **健康檢查**：每 30 秒檢查一次 `/` 端點
  - **Worker 數量**：預設 4 個（可透過 `WORKERS` 環境變數調整）
  - **系統依賴**：
    - `tesseract-ocr` + `tesseract-ocr-chi-tra`：中文繁體 OCR 支援
    - `libmagic1`：檔案類型偵測（unstructured 套件所需）
    - `poppler-utils`：PDF 處理和轉換
    - `pandoc`：DOCX/PPTX 文件轉換
    - `curl`：健康檢查工具
- **ollama**：本地 LLM 推理服務
  - **連接埠**：11434
  - **預設模型**：llama3
- **chromadb**：向量資料庫服務
  - **連接埠**：8001（避免與 FastAPI 的 8000 埠衝突）
  - **集合**：internal_sop
  - **嵌入維度**：由 Google embedding-001 模型決定

## 🤖 使用方式

### Slack 指令

在任何頻道中提及您的機器人：

```
@SunnetBot 我們公司的遠端工作政策是什麼？
@SunnetBot 如何設定開發環境？
@SunnetBot AI 領域的最新行業趋勢是什麼？
```

### API 端點

- `GET /` - 健康檢查端點
- `POST /slack/events` - Slack 事件 webhook
- `GET /docs` - API 文件（Swagger UI）

## 🧠 運作原理

### RAG 流水線流程

1. **接收問題**：使用者在 Slack 中提及機器人
2. **文件檢索**：使用向量相似度搜尋內部知識庫
3. **相關性評分**：AI 判斷檢索到的文件是否相關
4. **生成回答**：
   - 如果找到相關文件 → 從內部知識生成答案
   - 如果沒有相關文件 → 搜尋網路並生成答案
5. **知識儲存**：新資訊自動儲存到 Google Drive
6. **回答傳遞**：將最終答案傳回給 Slack 使用者

### 支援的文件類型

- **文字檔案**：`.txt`、`.md`、`.csv`
- **辦公文件**：`.docx`、`.pptx`、`.xlsx`
- **PDF 文件**：支援 OCR 的 `.pdf` 檔案
- **圖片檔案**：`.jpg`、`.png`、`.gif`（支援 OCR）
- **網頁內容**：URL 和網頁爬取功能

## 🔄 CI/CD 流水線

這個專案包含了完整的 GitHub Actions 流水線：

### 自動化測試
- ✅ 單元測試和整合測試
- ✅ 程式碼覆蓋率報告
- ✅ 程式碼檢查和格式化驗證
- ✅ 安全漏洞掃描

### 構建與部署
- 🏗️ Docker 鏡像構建
- 🧪 容器功能測試
- 🔒 使用 Trivy 進行安全掃描
- 📊 程式碼品質指標

### 觸發條件
- 推送到 `master` 或 `develop` 分支
- 向 `master` 分支發起 Pull Request
- 手動觸發工作流程

## 🔒 安全性

### 最佳實踐
- 🔐 使用環境變數儲存敏感資料
- 🛡️ 輸入驗證和清理
- 🔍 定期更新相依套件
- 📝 全面的日誌記錄，不暴露敏感資訊
- 🚨 自動化安全掃描

### Slack 安全性
- ✅ 所有要求的簽名驗證
- ✅ 機器人令牌驗證
- ✅ 限速保護
- ✅ 安全的 webhook 端點

## 🚀 生產環境部署

### Docker 部署

```bash
# 基本生產環境構建和啟動
docker-compose up -d

# 自定義配置運行（進階選項）
docker run -d \
  --name sunnetchat \
  -p 8000:8000 \
  --env-file .env.prod \
  -e PORT=8000 \
  -e WORKERS=4 \
  -e LOG_LEVEL=info \
  -v /path/to/docs:/app/local_documents \
  --user 1000:1000 \
  --restart unless-stopped \
  sunnetchat:latest

# 檢查健康狀態
docker inspect --format='{{.State.Health.Status}}' slack_agent_app
# 預期輸出：healthy

# 查看健康檢查日誌
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' slack_agent_app

# 調整 worker 數量以提升效能
docker run -d \
  -e WORKERS=8 \
  -p 8000:8000 \
  --env-file .env \
  sunnetchat:latest
```

### Docker 安全最佳實踐

本專案已實施以下安全措施：

- ✅ **非 root 執行**：容器以非特權用戶 `appuser` (UID 1000) 運行
- ✅ **多階段構建**：分離構建和運行環境，最小化攻擊面
- ✅ **健康檢查**：自動監控並重啟故障容器
- ✅ **.dockerignore**：防止敏感文件和不必要文件進入映像檔
- ✅ **最小依賴**：僅安裝運行時必需的系統套件
- ✅ **定期掃描**：CI/CD 流水線包含 Trivy 安全掃描

### 環境考量事項

- **資源需求**：最低 2GB 記憶體、2 CPU 核心
- **儲存空間**：向量資料庫需要持久化儲存
- **網路設定**：確保防火牆允許 Slack webhook 訪問
- **監控**：設定健康檢查和警告

## 🤝 貢獻指南

歡迎大家貢獻！請參閱我們的[貢獻指南](CONTRIBUTING.md)以獲取詳細資訊。

### 開發工作流程

1. Fork 這個儲存庫
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 進行修改
4. 為新功能新增測試
5. 確保所有測試通過 (`pytest`)
6. 提交修改 (`git commit -m 'Add amazing feature'`)
7. 推送到分支 (`git push origin feature/amazing-feature`)
8. 開啟 Pull Request

### 程式碼標準

- 遵循 PEP 8 編程風格指南
- 適當新增型別提示
- 編寫全面的測試
- 更新新功能的文件
- 確保 CI/CD 流水線通過

## 📚 文件

- **API 文件**：應用程式執行時可在 `/docs` 查看
- **系統架構**：參閱 `docs/architecture.md`
- **部署指南**：參閱 `docs/deployment.md`
- **問題排除**：參閱 `docs/troubleshooting.md`

## 🔧 問題排除

### 常見問題

#### 機器人無回應
```bash
# 檢查容器狀態
docker-compose ps

# 檢查日誌
docker-compose logs app

# 驗證 Slack webhook
curl -X POST http://localhost:8000/slack/events
```

#### 向量資料庫問題
```bash
# 重設 ChromaDB
docker-compose down -v
docker-compose up chromadb -d

# 重新匯入文件
python scripts/ingest.py
```

#### Ollama 模型問題
```bash
# 下載所需模型
docker exec -it ollama ollama pull llama3

# 列出可用模型
docker exec -it ollama ollama list
```

#### 容器健康檢查失敗
```bash
# 檢查容器健康狀態
docker inspect --format='{{.State.Health.Status}}' slack_agent_app
# 可能的狀態：healthy, unhealthy, starting

# 查看健康檢查日誌
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' slack_agent_app

# 手動測試健康檢查端點
curl http://localhost:8000/
# 應回應 JSON 格式的健康狀態

# 檢查容器日誌中的錯誤
docker logs slack_agent_app --tail 50

# 如果持續失敗，重啟容器
docker-compose restart app

# 完全重建（清除所有快取）
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**常見健康檢查失敗原因**：
- 應用程式啟動時間過長（等待 40 秒後重試）
- 環境變數配置錯誤（檢查 `.env` 檔案）
- 依賴服務未就緒（確認 ChromaDB 和 Ollama 正常運行）
- 連接埠衝突（確認 8000 埠未被佔用）

## 📈 效能最佳化

### 向量資料庫調整
- 調整區塊大小以改善檢索效果
- 最佳化嵌入維度
- 使用適當的索引策略

### LLM 效能
- 選擇適當的模型大小
- 實現回應快取
- 為長回應使用串流

### 擴展考量事項
- 使用負載均衡器實現水平擴展
- 使用 Redis 進行工作階段管理
- 考量多區域部署

## 📄 授權條款

此專案採用 MIT 授權條款 - 請參閱 [LICENSE](LICENSE) 檔案以獲取詳細資訊。

## 🙏 致謝

- **LangChain**：提供優秀的 RAG 框架
- **FastAPI**：提供高效能的 Web 框架
- **Slack**：提供全面的機器人平台
- **ChromaDB**：提供向量資料庫解決方案
- **Ollama**：提供本地 LLM 功能

## 📞 支援與聯繫

- **問題回報**：[GitHub Issues](https://github.com/trionnemesis/sunnetchat/issues)
- **討論區**：[GitHub Discussions](https://github.com/trionnemesis/sunnetchat/discussions)
- **電子郵件**：support@sunnetchat.com

---

<div align="center">
  <sub>由 SunnetChat 團隊用 ❤️ 精心打造</sub>
</div>