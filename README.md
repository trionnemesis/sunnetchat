# SunnetChat 智慧聊天機器人 🤖💬

[![CI/CD 流水線](https://github.com/trionnemesis/sunnetchat/actions/workflows/ci.yml/badge.svg)](https://github.com/trionnemesis/sunnetchat/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com)
[![授權條款: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 一個具備 RAG（檢索增強生成）功能的 AI Slack 聊天機器人，專為內部文件知識庫問答設計。

## 🌟 主要功能

- **🔍 智慧文件搜尋**：使用向量相似度搜尋從內部知識庫中檢索相關資訊。
- **⚡ 即時處理**：基於 FastAPI 構建，支援高效能非同步操作。
- **🔒 安全整合**：與 Slack 安全整合，保護企業內部資訊。
- **🐳 Docker 就緒**：使用 Docker Compose 完整容器化，簡化部署流程。

## 🏗️ 系統架構

```
┌──────────────┐       ┌────────────────┐      ┌───────────────┐
│  Slack User  │──────▶│  FastAPI App   │─────▶│  Core Agent   │
└──────────────┘       └────────────────┘      └───────────────┘
                                                       │
                                                       ▼
                                             ┌────────────────┐
                                             │  RAG Pipeline  │
                                             └────────────────┘
                                                       │
                       ┌───────────────────────────────┼───────────────────────────────┐
                       │                               │                               │
                       ▼                               ▼                               ▼
            ┌────────────────┐             ┌────────────────┐             ┌──────────────────┐
            │    ChromaDB    │             │     Ollama     │             │ Google Embeddings│
            │ (Vector Store) │             │     (LLM)      │             │ (Text Embedding) │
            └────────────────┘             └────────────────┘             └──────────────────┘
```

## 🚀 快速開始

### 前置需求

- Docker 和 Docker Compose
- Python 3.11+
- 一個 Slack 應用程式及 Bot Token
- Google API 憑證 (用於嵌入模型)

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

# Google Embeddings API 金鑰
EMBEDDING_MODEL="models/embedding-001"
GOOGLE_API_KEY="your-google-api-key"

# 本地文件知識庫路徑 (可選)
SOURCE_DOCS_PATH="./local_documents"
```

### 3. 將您的文件放入 `local_documents`

將您希望機器人學習的文件（如 `.txt`, `.pdf`, `.docx`）放入專案根目錄下的 `local_documents` 資料夾。

### 4. 使用 Docker 啟動

```bash
# 啟動所有服務 (包含資料庫和 LLM)
docker-compose up -d --build

# 檢查服務狀態
docker-compose ps

# 查看應用程式日誌
docker-compose logs -f app
```

### 5. 匯入知識庫文件

當服務啟動後，執行以下指令來匯入您的文件到向量資料庫：

```bash
docker-compose exec app python scripts/ingest.py
```

### 6. 設定 Slack

1.  在 [api.slack.com](https://api.slack.com/apps) 建立一個 Slack 應用程式。
2.  啟用 **Socket Mode**。
3.  啟用 **Event Subscriptions**，並訂閱 `app_mention` 事件。
4.  將應用程式安裝到您的工作區。
5.  邀請機器人到您想使用的頻道中：`/invite @您的機器人名稱`

## 🧪 開發指南

### 本地開發環境

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝相依套件
pip install -r requirements.txt

# 啟動後端服務
docker-compose up chromadb ollama -d

# 執行 FastAPI 應用程式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 執行測試與品質檢查

```bash
# 執行所有測試
pytest

# 格式化程式碼
black .

# 程式碼品質檢查
flake8 .
```

## 📁 專案結構

```
sunnetchat/
├── 📁 app/                 # 主要應用程式原始碼
│   ├── 🐍 main.py         # FastAPI 應用程式與 Slack 事件處理
│   ├── 🧠 core_agent.py    # 核心代理與 RAG 邏輯
│   └── ⚙️ rag_core.py     # RAG 核心功能
├── 🧪 tests/              # 測試程式碼
├── 📁 scripts/           # 工具腳本
│   └── 🐍 ingest.py      # 文件匯入腳本
├── 🔧 .github/workflows/ # CI/CD 工作流程
├── 🐳 docker-compose.yml # Docker Compose 設定
├── 🐳 Dockerfile        # 應用程式容器設定
├── 📋 requirements.txt   # Python 相依套件
└── 📖 README.md         # 本文件
```

## 🔧 環境變數

| 變數名稱 | 描述 | 必要性 | 預設值 |
|---|---|---|---|
| `SLACK_BOT_TOKEN` | Slack 機器人的 OAuth Token | ✅ | - |
| `SLACK_SIGNING_SECRET` | Slack 應用程式簽名秘鑰 | ✅ | - |
| `EMBEDDING_MODEL` | Google 嵌入模型的名稱 | ❌ | `models/embedding-001` |
| `GOOGLE_API_KEY` | Google API 金鑰 | ✅ | - |
| `SOURCE_DOCS_PATH` | 本地文件存放路徑 | ❌ | `/app/local_documents` |
| `CHROMA_HOST` | ChromaDB 主機位址 | ❌ | `chromadb` |
| `CHROMA_PORT` | ChromaDB 連接埠 | ❌ | `8000` |
| `OLLAMA_BASE_URL` | Ollama 服務 URL | ❌ | `http://ollama:11434` |
| `OLLAMA_MODEL` | Ollama 模型名稱 | ❌ | `llama3` |

## 🙏 致謝

- **LangChain**
- **FastAPI**
- **Slack**
- **ChromaDB**
- **Ollama**
