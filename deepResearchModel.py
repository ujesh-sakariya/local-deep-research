# --- Imports ---
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_tavily import TavilySearch
from langchain.chains import RetrievalQA
from langchain.agents import Tool, initialize_agent

from local_deep_research.api import quick_summary  # <-- ✅ added summarization module

from dotenv import load_dotenv
import os

# --- Step 1: Environment setup ---
load_dotenv()

# --- Step 2: Load and split documents ---
folder_path = 'local_collections/'
all_docs = []

for filename in os.listdir(folder_path):
    if filename.lower().endswith('.pdf'):
        full_path = os.path.join(folder_path, filename)
        loader = PyPDFLoader(full_path)
        docs = loader.load()
        all_docs.extend(docs)

# Split the docs
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
split_docs = text_splitter.split_documents(all_docs)

# Optional: Summarize chunks before embedding (use only if summarization quality is high)
# for doc in split_docs:
#     doc.page_content = quick_summary(doc.page_content)

# --- Step 3: Embedding and Retrieval ---
embedding = OllamaEmbeddings(model='llama3')
vectorStore = Chroma.from_documents(split_docs, embedding)
retriever = vectorStore.as_retriever()

# --- Step 4: Local Document QA Tool ---
llm = OllamaLLM(model="gemma3:12b")
qa_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

local_doc_tool = Tool(
    name="LocalDocumentQA",
    func=qa_chain.run,
    description="Useful for answering questions based on local documents."
)

# --- Step 5: Web Search Tool (summarized) ---
raw_tavily_tool = TavilySearch(k=3, api_key=os.getenv("TAVILY_API_KEY"))

def web_search_wrapper(query: str) -> str:
    raw_results = raw_tavily_tool.invoke(query)
    summary = quick_summary(raw_results)  # ✅ summarize web search results
    return summary

web_tool = Tool(
    name="WebSearch",
    func=web_search_wrapper,
    description="Useful for searching the web when local documents don't have the answer."
)

# --- Step 6: Create agent ---
tools = [local_doc_tool, web_tool]

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)

# --- Step 7: Ask a question ---
question = "What is the most impressive project of this?"
response = agent.run(question)

# Optional: Summarize final response
final_summary = quick_summary(response)  # ✅ summarizing agent's answer

print("\n🔎 Agent Full Answer:\n", response)
print("\n🧠 Summarized Insight:\n", final_summary)
