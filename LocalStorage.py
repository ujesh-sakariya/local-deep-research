from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from local_deep_research.api import quick_summary
from langchain_community.document_loaders import PyPDFLoader
import os
print("Current working directory:", os.getcwd())
print(f"Looking for PDFs in: {'local_collections/'}")

for filename in os.listdir('local_collections/'):
    print(f"Found file: {filename}")
    if filename.lower().endswith('.pdf'):
        print(f"Processing PDF: {filename}")

all_docs = []
folder_path = 'local_collections/'
for filename in os.listdir('local_collections/'):
    if filename.lower().endswith('.pdf'): # procees PDF's now 
        full_path = os.path.join(folder_path,filename)
        loader = PyPDFLoader(full_path) #chunks the pdf
        docs = loader.load()
        all_docs.extend(docs)

print(f"Total chunks loaded: {len(all_docs)}")
print(f"Sample chunk text: {all_docs[0].page_content[:500]}")

# Create your retriever (any LangChain retriever works)

embedding = OllamaEmbeddings(model='llama3') # create the embedding function
vectorstore = FAISS.from_documents(all_docs, embedding)
retriever = vectorstore.as_retriever()

# Use with LDR
result = quick_summary(
    query="give a summary of this candidates CV",
    retrievers={"doc": retriever},
    search_tool="doc"
)

print(result)