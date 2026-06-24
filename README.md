# 🌱 Groot RAG Assistant

A production-ready Retrieval Augmented Generation (RAG) assistant built with FastAPI, LangGraph, FAISS, PostgreSQL, Redis, and Qwen 2.5.

The system supports document understanding, OCR, semantic search, tabular analytics, conversation memory, follow-up reasoning, and web search fallback through a custom chat interface.

---

# ✨ Features

### 🤖 AI Assistant

* Multi-turn conversations
* Context-aware follow-up handling
* Persistent chat history
* Automatic conversation titles
* Long-term memory summarization

### 📄 Document Intelligence

Supports:

* PDF
* DOCX
* TXT
* PNG
* JPG
* JPEG
* CSV
* XLSX
* XLS

### 🔍 OCR Processing

Automatic OCR for:

* Scanned PDFs
* Images
* Non-searchable documents

Powered by Tesseract OCR.

### 🧠 Conversation Memory

#### Short-Term Memory

* Redis-backed message cache
* Low-latency retrieval
* Automatic PostgreSQL fallback

#### Long-Term Memory

* Incremental conversation summaries
* Context preservation across long chats
* Memory-aware follow-up responses

### 📚 Retrieval Augmented Generation

* Semantic chunking
* FAISS vector search
* Embedding-based retrieval
* Similarity scoring
* Source-aware responses

### 📊 Spreadsheet Analytics

Natural language analytics over:

* Excel files
* CSV files

Supports:

* Sum
* Average
* Count
* Maximum
* Minimum
* Median
* Variance
* Standard Deviation

Also supports SQL queries directly against uploaded datasets.

### 🌐 Web Search Fallback

When retrieval quality is insufficient:

* DuckDuckGo search
* Automatic web scraping
* Context augmentation

### ⚡ LangGraph Routing

Automatically routes requests to:

* General chat
* Document retrieval
* Follow-up conversations
* Spreadsheet analytics
* Web search
* Knowledge questions

---

# 🏗 System Architecture

```text
                    ┌─────────────────────┐
                    │     Frontend        │
                    │ HTML + CSS + JS     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │   backend_server    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      LangGraph      │
                    │   Routing Engine    │
                    └──────────┬──────────┘
                               │
      ┌────────────────────────┼────────────────────────┐
      │                        │                        │
      ▼                        ▼                        ▼

┌───────────────┐     ┌────────────────┐     ┌────────────────┐
│ Memory Layer  │     │ Retrieval Layer│     │ Analytics Layer│
├───────────────┤     ├────────────────┤     ├────────────────┤
│ Redis         │     │ FAISS          │     │ Pandas         │
│ PostgreSQL    │     │ MiniLM Embed   │     │ SQLite         │
└───────────────┘     └────────────────┘     └────────────────┘

                               │
                               ▼

                    ┌─────────────────────┐
                    │  Qwen 2.5-3B        │
                    │  Kaggle GPU Server  │
                    │  Exposed via Ngrok  │
                    └─────────────────────┘
```

---

# 🛠 Technology Stack

## Backend

* FastAPI
* LangGraph
* LangChain
* SQLAlchemy

## LLM

* Qwen2.5-3B-Instruct
* Kaggle GPU Deployment
* Ngrok API Gateway

## Embeddings

* sentence-transformers/all-MiniLM-L6-v2

## Vector Database

* FAISS

## Database

* PostgreSQL

## Cache

* Redis

## Data Processing

* Pandas
* OpenPyXL
* SQLite

## OCR

* Tesseract OCR
* PDF2Image

## Search

* DuckDuckGo Search
* BeautifulSoup Web Scraping

## Frontend

* HTML
* CSS
* JavaScript

---

# 📂 Project Structure

```text
groot-rag-assistant/

├── backend.py
├── backend_server.py
├── db.py
├── memory_cache.py
│
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── faiss_indexes/
├── requirements.txt
├── README.md
└── .env
```

---

# ⚙️ Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/groot

REDIS_URL=redis://localhost:6379/0

NGROK_URL=https://your-ngrok-url.ngrok-free.app

APP_API_KEY=your_api_key
```

---

# 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/Kuldeep-amreliya/groot-rag-assistant.git

cd groot-rag-assistant
```

Create virtual environment:

```bash
python -m venv myenv
```

Windows:

```bash
myenv\Scripts\activate
```

Linux / macOS:

```bash
source myenv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Backend

```bash
python backend_server.py
```

or

```bash
uvicorn backend_server:app --host 0.0.0.0 --port 7860
```

Open:

```text
http://localhost:7860
```

---

# 📌 Example Queries

### Document QA

```text
Summarize this PDF.

What are the key findings?

Who is mentioned in this document?
```

### Spreadsheet Analytics

```text
What is the average revenue?

How many rows exist?

Which record has the highest value?
```

### SQL Query

```sql
SELECT * FROM sales
WHERE revenue > 100000
```

### Follow-Up Question

```text
Explain LangGraph.

How is it different from LangChain?
```

The assistant automatically uses previous conversation context.

---

# 🔮 Future Improvements

* Streaming responses
* User authentication
* Docker deployment
* Hybrid retrieval (BM25 + Vector Search)
* Citation highlighting
* Multi-model support
* Kubernetes deployment

---

# 👨‍💻 Author

Kuldeep Amareliya

AI/ML Engineer

GitHub:
https://github.com/Kuldeep-amreliya

LinkedIn:
https://www.linkedin.com/in/k-amreliya

---
