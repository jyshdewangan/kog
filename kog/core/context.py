import os
import json
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader, PyPDFLoader
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from kog.core.config import config

class ContextManager:
    def __init__(self):
        self.embeddings = OllamaEmbeddings(model="qwen2.5:3b")
        self.collection_name = "kog_contexts"
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(config.chroma_dir)
        )
        self.contexts_file = config.contexts_file

    def _load_data(self) -> dict:
        try:
            with open(self.contexts_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"contexts": {}}

    def _save_data(self, data: dict):
        with open(self.contexts_file, "w") as f:
            json.dump(data, f, indent=4)

    def add_context(self, file_path: str, context_name: Optional[str] = None) -> str:
        """Reads a file, chunks it, embeds it into ChromaDB, and saves metadata."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")

        if not context_name:
            context_name = path.stem

        if path.suffix == ".md":
            loader = UnstructuredMarkdownLoader(str(path))
        elif path.suffix == ".pdf":
            loader = PyPDFLoader(str(path))
        else:
            loader = TextLoader(str(path))
            
        docs = loader.load()
        for doc in docs:
            doc.metadata["context_name"] = context_name
            doc.metadata["source"] = str(path)

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        if not splits:
            raise ValueError(f"No text extracted from {file_path}. Is the file empty?")
            
        self.vectorstore.add_documents(documents=splits)
        
        # update metadata mapping
        data = self._load_data()
        data.setdefault("contexts", {})[context_name] = {"source": str(path)}
        self._save_data(data)
        
        return context_name

    def list_contexts(self) -> dict:
        return self._load_data().get("contexts", {})

    def delete_context(self, context_name: str) -> bool:
        data = self._load_data()
        if context_name in data.get("contexts", {}):
            # Try to delete from chroma
            # Chroma doesn't easily let us delete by metadata filter directly without retrieving IDs
            # but we can get it via vectorstore.get()
            results = self.vectorstore.get(where={"context_name": context_name})
            if results and results.get("ids"):
                self.vectorstore.delete(ids=results["ids"])
            
            del data["contexts"][context_name]
            self._save_data(data)
            return True
        return False
        
    def get_retriever(self, context_names: List[str]):
        """Returns a retriever filtering for the specified context names."""
        if not context_names:
            raise ValueError("No contexts loaded in session.")
            
        if len(context_names) == 1:
            filter_dict = {"context_name": context_names[0]}
        else:
            filter_dict = {"context_name": {"$in": context_names}}
            
        return self.vectorstore.as_retriever(
            search_kwargs={"filter": filter_dict, "k": 5}
        )

context_manager = ContextManager()
