# SunnetChat 🤖💬

[![CI/CD Pipeline](https://github.com/trionnemesis/sunnetchat/actions/workflows/ci.yml/badge.svg)](https://github.com/trionnemesis/sunnetchat/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An intelligent AI-powered Slack chatbot with advanced RAG (Retrieval-Augmented Generation) capabilities for document processing, knowledge management, and real-time information retrieval.

## 🌟 Features

### Core Capabilities
- **🔍 Intelligent Document Search**: Retrieves relevant information from your internal knowledge base using vector similarity search
- **🌐 Web Search Integration**: Falls back to live web search when internal documents don't contain the answer
- **📚 Knowledge Storage**: Automatically saves new knowledge to Google Drive for future reference
- **⚡ Real-time Processing**: Built with FastAPI for high-performance async operations
- **🔒 Enterprise Security**: Secure Slack integration with proper authentication

### RAG Pipeline
- **Vector Embeddings**: Uses Google's `embedding-001` model for semantic understanding
- **Document Grading**: Intelligent relevance scoring to determine best information sources
- **Multi-modal Search**: Supports text, images, PDFs, DOCX, PPTX, and more
- **Conversation Flow**: LangGraph-powered conversation management

### Deployment & Scaling
- **🐳 Docker Ready**: Full containerization with Docker Compose
- **🚀 Production Ready**: Optimized for deployment with health checks and monitoring
- **🔄 CI/CD Pipeline**: Comprehensive testing, security scanning, and automated deployment
- **📊 Observability**: Built-in logging and error handling

## 🏗️ Architecture

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

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Slack App with Bot Token
- Google API Credentials (for Drive & Embeddings)
- Tavily API Key (for web search)

### 1. Clone & Setup

```bash
git clone https://github.com/trionnemesis/sunnetchat.git
cd sunnetchat
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your credentials:

```bash
# Slack Configuration
SLACK_BOT_TOKEN="xoxb-your-bot-token-here"
SLACK_SIGNING_SECRET="your-slack-signing-secret-here"

# Google Services
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_DRIVE_FOLDER_ID="your-google-drive-folder-id"
GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type": "service_account", ...}'

# Tavily Web Search
TAVILY_API_KEY="tvly-your-tavily-api-key"

# Local Knowledge Base
LOCAL_KNOWLEDGE_BASE_PATH="/path/to/your/documents"
```

### 3. Launch with Docker

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 4. Setup Slack Integration

1. Create a Slack App at [api.slack.com](https://api.slack.com/apps)
2. Enable Event Subscriptions: `http://your-domain.com/slack/events`
3. Subscribe to `app_mention` events
4. Install app to workspace
5. Invite bot to channels: `/invite @YourBot`

## 🧪 Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start services separately
docker-compose up chromadb ollama -d

# Run app locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run integration tests
pytest tests/test_slack_integration.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking (if using mypy)
mypy app/
```

## 📁 Project Structure

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
├── 🐳 Dockerfile            # Application container
├── 📋 requirements.txt       # Python dependencies
└── 📖 README.md             # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | ✅ | - |
| `SLACK_SIGNING_SECRET` | Slack App Signing Secret | ✅ | - |
| `GOOGLE_API_KEY` | Google API Key for Embeddings | ✅ | - |
| `GOOGLE_DRIVE_FOLDER_ID` | Google Drive folder for storage | ✅ | - |
| `TAVILY_API_KEY` | Tavily API key for web search | ✅ | - |
| `LOCAL_KNOWLEDGE_BASE_PATH` | Path to local documents | ❌ | `/app/local_documents` |
| `CHROMA_HOST` | ChromaDB host | ❌ | `chromadb` |
| `CHROMA_PORT` | ChromaDB port | ❌ | `8000` |
| `OLLAMA_BASE_URL` | Ollama service URL | ❌ | `http://ollama:11434` |
| `LLM_MODEL` | Ollama model name | ❌ | `llama3` |

### Docker Services

- **app**: Main FastAPI application (Port: 8000)
- **ollama**: Local LLM service (Port: 11434)
- **chromadb**: Vector database (Port: 8001)

## 🤖 Usage

### Slack Commands

Mention your bot in any channel:

```
@SunnetBot What is our company policy on remote work?
@SunnetBot How do I set up the development environment?
@SunnetBot What are the latest industry trends in AI?
```

### API Endpoints

- `GET /` - Health check endpoint
- `POST /slack/events` - Slack events webhook
- `GET /docs` - API documentation (Swagger UI)

## 🧠 How It Works

### RAG Pipeline Flow

1. **Question Reception**: User mentions bot in Slack
2. **Document Retrieval**: Searches internal knowledge base using vector similarity
3. **Relevance Grading**: AI determines if retrieved documents are relevant
4. **Response Generation**: 
   - If relevant documents found → Generate answer from internal knowledge
   - If no relevant documents → Search web and generate answer
5. **Knowledge Storage**: New information automatically saved to Google Drive
6. **Response Delivery**: Final answer sent back to Slack user

### Supported Document Types

- **Text**: `.txt`, `.md`, `.csv`
- **Office**: `.docx`, `.pptx`, `.xlsx`
- **PDF**: `.pdf` files with OCR support
- **Images**: `.jpg`, `.png`, `.gif` (with OCR)
- **Web**: URLs and web scraping capabilities

## 🔄 CI/CD Pipeline

The project includes a comprehensive GitHub Actions pipeline:

### Automated Testing
- ✅ Unit and integration tests
- ✅ Code coverage reporting
- ✅ Linting and formatting checks
- ✅ Security vulnerability scanning

### Build & Deploy
- 🏗️ Docker image building
- 🧪 Container functionality testing
- 🔒 Security scanning with Trivy
- 📊 Code quality metrics

### Triggers
- Push to `master` or `develop` branches
- Pull requests to `master`
- Manual workflow dispatch

## 🔒 Security

### Best Practices
- 🔐 Environment variables for sensitive data
- 🛡️ Input validation and sanitization
- 🔍 Regular dependency updates
- 📝 Comprehensive logging without exposing secrets
- 🚨 Automated security scanning

### Slack Security
- ✅ Signature verification for all requests
- ✅ Bot token validation
- ✅ Rate limiting protection
- ✅ Secure webhook endpoints

## 🚀 Production Deployment

### Docker Deployment

```bash
# Production build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With custom configuration
docker run -d \
  --name sunnetchat \
  -p 8000:8000 \
  --env-file .env.prod \
  -v /path/to/docs:/app/local_documents \
  sunnetchat:latest
```

### Environment Considerations

- **Resource Requirements**: Minimum 2GB RAM, 2 CPU cores
- **Storage**: Vector database requires persistent storage
- **Network**: Ensure firewall allows Slack webhook access
- **Monitoring**: Set up health checks and alerting

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints where appropriate
- Write comprehensive tests
- Update documentation for new features
- Ensure CI/CD pipeline passes

## 📚 Documentation

- **API Docs**: Available at `/docs` when running the application
- **Architecture**: See `docs/architecture.md`
- **Deployment**: See `docs/deployment.md`
- **Troubleshooting**: See `docs/troubleshooting.md`

## 🔧 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs app

# Verify Slack webhook
curl -X POST http://localhost:8000/slack/events
```

#### Vector Database Issues
```bash
# Reset ChromaDB
docker-compose down -v
docker-compose up chromadb -d

# Re-ingest documents
python scripts/ingest.py
```

#### Ollama Model Issues
```bash
# Pull required model
docker exec -it ollama ollama pull llama3

# List available models
docker exec -it ollama ollama list
```

## 📈 Performance Optimization

### Vector Database Tuning
- Adjust chunk sizes for better retrieval
- Optimize embedding dimensions
- Use proper indexing strategies

### LLM Performance
- Choose appropriate model sizes
- Implement response caching
- Use streaming for long responses

### Scaling Considerations
- Implement horizontal scaling with load balancers
- Use Redis for session management
- Consider multi-region deployment

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain**: For the excellent RAG framework
- **FastAPI**: For the high-performance web framework  
- **Slack**: For the comprehensive bot platform
- **ChromaDB**: For the vector database solution
- **Ollama**: For local LLM capabilities

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/trionnemesis/sunnetchat/issues)
- **Discussions**: [GitHub Discussions](https://github.com/trionnemesis/sunnetchat/discussions)
- **Email**: support@sunnetchat.com

---

<div align="center">
  <sub>Built with ❤️ by the SunnetChat team</sub>
</div>