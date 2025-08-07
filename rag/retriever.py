import os
from typing import List, Dict, Optional
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

class KnowledgeRetriever:
    """Retrieves relevant information from domain-specific knowledge bases"""
    
    def __init__(self, vectorstore_dir="rag/vectorstores"):
        self.vectorstore_dir = vectorstore_dir
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self._vectorstores = {}  # Cache for loaded vectorstores
    
    def _load_vectorstore(self, domain: str) -> Optional[Chroma]:
        """Load vectorstore for a specific domain"""
        if domain in self._vectorstores:
            return self._vectorstores[domain]
        
        vectorstore_path = os.path.join(self.vectorstore_dir, domain)
        
        if not os.path.exists(vectorstore_path):
            print(f"Warning: No knowledge base found for domain '{domain}'")
            return None
        
        try:
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings,
                collection_name=f"{domain}_knowledge"
            )
            self._vectorstores[domain] = vectorstore
            return vectorstore
        except Exception as e:
            print(f"Error loading vectorstore for {domain}: {e}")
            return None
    
    def retrieve_knowledge(self, domain: str, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve relevant knowledge for a query from domain-specific knowledge base"""
        vectorstore = self._load_vectorstore(domain)
        
        if not vectorstore:
            return []
        
        try:
            # Perform similarity search
            docs = vectorstore.similarity_search_with_score(query, k=top_k)
            
            # Format results
            results = []
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source_file", "unknown"),
                    "domain": doc.metadata.get("domain", domain),
                    "relevance_score": float(score)
                })
            
            return results
            
        except Exception as e:
            print(f"Error retrieving knowledge for {domain}: {e}")
            return []
    
    def get_context_string(self, domain: str, query: str, top_k: int = 3) -> str:
        """Get formatted context string for prompts"""
        results = self.retrieve_knowledge(domain, query, top_k)
        
        if not results:
            return ""
        
        context_parts = []
        context_parts.append(f"[Relevant knowledge from {domain} domain:]")
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"{i}. {result['content'][:400]}...")
            context_parts.append(f"   Source: {result['source']}")
        
        return "\n".join(context_parts)
    
    def available_domains(self) -> List[str]:
        """Get list of available knowledge domains"""
        if not os.path.exists(self.vectorstore_dir):
            return []
        
        domains = []
        for item in os.listdir(self.vectorstore_dir):
            domain_path = os.path.join(self.vectorstore_dir, item)
            if os.path.isdir(domain_path):
                domains.append(item)
        
        return domains

# Test the retriever
if __name__ == "__main__":
    retriever = KnowledgeRetriever()
    
    # Test retrieval
    test_queries = [
        ("medical", "AI diagnostic accuracy"),
        ("tech", "AI market growth"),
        ("ethics", "fairness in AI systems")
    ]
    
    print("🔍 Testing Knowledge Retrieval:")
    print("=" * 50)
    
    for domain, query in test_queries:
        print(f"\nDomain: {domain}")
        print(f"Query: {query}")
        print("-" * 30)
        
        context = retriever.get_context_string(domain, query, top_k=2)
        if context:
            print(context)
        else:
            print("No relevant knowledge found")
        print()
