# 🔍 Deep Research Model

This project allows you to perform question answering using both **local PDF documents** and **live web search**. It combines document retrieval, summarisation, and LLM inference using LangChain, Ollama, and Tavily.

---

## 📦 Setup Instructions

In the  `deepResearchModel.py`

### 1. Prepare Local Documents
Place all your `.pdf` files in a folder named:

```
local_collections/
```

> ⚙️ You can change this folder name by editing the path in `deepResearchModel.py`.

---

### 2. Install Requirements

Create and activate your virtual environment, then install dependencies:

```
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Set Your Environment Variables

Export your **Tavily API key**:

```
export TAVILY_API_KEY=your_api_key_here
```
---
### 4. Download Ollama Model

Ensure you have **Ollama** installed and the model used in the code (default: `llama3`) is downloaded:

```
ollama run llama3
```
---

### 5. Run the Model

Call the main function from your Python script or an interactive shell:

```python
from deepResearchModel import run_question_answering

response, summary = run_question_answering("What is the most impressive project?")
print("Full Answer:\n", response)
print("\nSummary:\n", summary)
```

---

## ✅ Features

- Local document search (PDFs)
- Web search fallback (Tavily)
- LLM-based summarization and reasoning
- Modular LangChain agent system

---

## 🧠 Requirements

- Python 3.8+
- Ollama
- Tavily API key
- LangChain ecosystem
