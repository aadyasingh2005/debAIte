import os
import json
from pathlib import Path
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader, TextLoader  # ✅ Updated import
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma  # ✅ Updated import
from dotenv import load_dotenv

load_dotenv()

class RAGIndexer:
    """Creates and manages knowledge base indexes for different agent domains"""
    
    def __init__(self, docs_dir="rag/docs", vectorstore_dir="rag/vectorstores"):
        self.docs_dir = Path(docs_dir)
        self.vectorstore_dir = Path(vectorstore_dir)
        self.vectorstore_dir.mkdir(exist_ok=True)
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # Text splitter configuration
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_documents_from_domain(self, domain: str) -> List:
        """Load all documents from a specific domain directory"""
        domain_path = self.docs_dir / domain
        if not domain_path.exists():
            print(f"Warning: Domain directory {domain_path} does not exist")
            return []
        
        documents = []
        
        # Load PDF files
        for pdf_file in domain_path.glob("*.pdf"):
            try:
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()
                # Add metadata
                for doc in docs:
                    doc.metadata.update({
                        "domain": domain,
                        "source_file": pdf_file.name,
                        "file_type": "pdf"
                    })
                documents.extend(docs)
                print(f"Loaded PDF: {pdf_file.name} ({len(docs)} pages)")
            except Exception as e:
                print(f"Error loading PDF {pdf_file}: {e}")
        
        # Load text files
        for txt_file in domain_path.glob("*.txt"):
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                docs = loader.load()
                # Add metadata
                for doc in docs:
                    doc.metadata.update({
                        "domain": domain,
                        "source_file": txt_file.name,
                        "file_type": "txt"
                    })
                documents.extend(docs)
                print(f"Loaded text file: {txt_file.name}")
            except Exception as e:
                print(f"Error loading text file {txt_file}: {e}")
        
        return documents
    
    def create_domain_index(self, domain: str, force_rebuild: bool = False):
        """Create or update vector index for a specific domain"""
        vectorstore_path = self.vectorstore_dir / domain
        
        # Check if index already exists
        if vectorstore_path.exists() and not force_rebuild:
            print(f"Index for {domain} already exists. Use force_rebuild=True to recreate.")
            return
        
        print(f"\n🔍 Creating knowledge base index for: {domain}")
        print("-" * 50)
        
        # Load documents
        documents = self.load_documents_from_domain(domain)
        
        if not documents:
            print(f"No documents found for domain: {domain}")
            return
        
        # Split documents into chunks
        print(f"Splitting {len(documents)} documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"Created {len(chunks)} text chunks")
        
        # Create embeddings and vector store
        print("Creating embeddings and vector store...")
        try:
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=str(vectorstore_path),
                collection_name=f"{domain}_knowledge"
            )
            
            # Persist the vector store
            vectorstore.persist()
            
            # Save metadata
            metadata = {
                "domain": domain,
                "document_count": len(documents),
                "chunk_count": len(chunks),
                "created_at": str(Path().cwd()),
                "source_files": [doc.metadata.get("source_file", "unknown") for doc in documents]
            }
            
            with open(vectorstore_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Successfully created index for {domain}")
            print(f"   Documents: {len(documents)}")
            print(f"   Chunks: {len(chunks)}")
            print(f"   Stored in: {vectorstore_path}")
            
        except Exception as e:
            print(f"❌ Error creating index for {domain}: {e}")
    
    def create_all_indexes(self, force_rebuild: bool = False):
        """Create indexes for all available domains"""
        domains = [d.name for d in self.docs_dir.iterdir() if d.is_dir()]
        
        if not domains:
            print("No domain directories found in rag/docs/")
            return
        
        print(f"Found domains: {', '.join(domains)}")
        
        for domain in domains:
            self.create_domain_index(domain, force_rebuild)
            print()  # Add spacing between domains
    
    def list_available_indexes(self) -> Dict[str, Dict]:
        """List all available indexes with metadata"""
        indexes = {}
        
        for domain_dir in self.vectorstore_dir.iterdir():
            if domain_dir.is_dir():
                metadata_file = domain_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                        indexes[domain_dir.name] = metadata
                    except Exception as e:
                        indexes[domain_dir.name] = {"error": str(e)}
                else:
                    indexes[domain_dir.name] = {"status": "no metadata"}
        
        return indexes

def main():
    """Command-line interface for the indexer"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Knowledge Base Indexer")
    parser.add_argument("--domain", help="Index specific domain only")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild existing indexes")
    parser.add_argument("--list", action="store_true", help="List available indexes")
    
    args = parser.parse_args()
    
    indexer = RAGIndexer()
    
    if args.list:
        indexes = indexer.list_available_indexes()
        print("\n📚 Available Knowledge Base Indexes:")
        print("=" * 50)
        for domain, metadata in indexes.items():
            print(f"Domain: {domain}")
            if "error" in metadata:
                print(f"  Status: Error - {metadata['error']}")
            elif "document_count" in metadata:
                print(f"  Documents: {metadata['document_count']}")
                print(f"  Chunks: {metadata['chunk_count']}")
                print(f"  Sources: {', '.join(metadata['source_files'][:3])}{'...' if len(metadata['source_files']) > 3 else ''}")
            else:
                print(f"  Status: {metadata.get('status', 'unknown')}")
            print()
    
    elif args.domain:
        indexer.create_domain_index(args.domain, args.rebuild)
    
    else:
        indexer.create_all_indexes(args.rebuild)

if __name__ == "__main__":
    main()
