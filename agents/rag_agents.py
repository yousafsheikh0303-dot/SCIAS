import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR = "db/chroma_store"
DOCS_DIR = "data/documents"

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load once, reuse across all rag_query() calls instead of reloading every time
_vectorstore = None


def build_vectorstore():
    """Run this once to ingest PDFs into ChromaDB. Re-run if you add new documents."""
    all_docs = []
    for filename in os.listdir(DOCS_DIR):
        if filename.lower().endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(DOCS_DIR, filename))
            pages = loader.load()

            # Skip pages that are just a table of contents -- these generic
            # section-header chunks were winning retrieval slots over real content.
            pages = [p for p in pages if "table of contents" not in p.page_content.lower()[:200]]

            all_docs.extend(pages)

    print(f"Loaded {len(all_docs)} pages from {DOCS_DIR}")

    # Larger chunk size so a fact and its section heading are less likely
    # to get split across two separate chunks.
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    chunks = splitter.split_documents(all_docs)
    print(f"Split into {len(chunks)} chunks")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA_DIR
    )
    print("Vectorstore built and persisted.")
    return vectorstore


def load_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embedding_model)
    return _vectorstore


def rag_query(question: str, k: int = 6) -> dict:
    vectorstore = load_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    relevant_docs = retriever.invoke(question)

    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Keep filename + page together so debugging retrieval is easier
    sources = list(set([
        f"{doc.metadata.get('source', 'unknown')} (page {doc.metadata.get('page', '?')})"
        for doc in relevant_docs
    ]))

    llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)

    prompt = f"""You are an agricultural advisory assistant. Answer the farmer's question using ONLY the context below.
If the context doesn't contain the answer, say so honestly.

Context:
{context}

Question: {question}

Answer:"""

    response = llm.invoke(prompt)
    return {
        "answer": response.content,
        "sources": sources
    }


if __name__ == "__main__":
    build_vectorstore()