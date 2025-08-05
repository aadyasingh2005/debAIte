import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Default creative config (no length limits)
CREATIVE_CONFIG = genai.GenerationConfig(
    temperature=0.7,
    max_output_tokens=500,
    top_p=0.95,
    top_k=40
)

def get_creative_config(stage=None, word_limits=None):
    """Get generation config with optional length limits"""
    if not word_limits:
        return CREATIVE_CONFIG
    
    max_tokens = word_limits.get(stage, {"tokens": 500})["tokens"]
    return genai.GenerationConfig(
        temperature=0.7,
        max_output_tokens=max_tokens,
        top_p=0.95,
        top_k=40
    )

class DebateAgent:
    def __init__(self, name, persona, role, expertise="", style="", knowledge_domain=None):
        self.name = name
        self.persona = persona
        self.role = role
        self.expertise = expertise
        self.style = style
        self.knowledge_domain = knowledge_domain or self._map_role_to_domain()
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Initialize RAG retriever (lazy loading)
        self._knowledge_retriever = None

    def _map_role_to_domain(self):
        """Automatically map agent role to knowledge domain"""
        role_to_domain = {
            "medical researcher": "medical",
            "doctor": "medical", 
            "physician": "medical",
            "healthcare": "medical",
            
            "startup founder": "tech",
            "engineer": "tech",
            "entrepreneur": "tech",
            "developer": "tech",
            "cto": "tech",
            
            "philosopher": "ethics",
            "ethicist": "ethics",
            "social activist": "ethics",
            "activist": "ethics",
            
            "lawyer": "legal",
            "attorney": "legal",
            "legal scholar": "legal",
            "judge": "legal",
            
            "economist": "economics",
            "business analyst": "economics",
            "financial analyst": "economics",
            "market researcher": "economics"
        }
        
        role_lower = self.role.lower()
        for key, domain in role_to_domain.items():
            if key in role_lower:
                return domain
        
        return None  # No domain mapping found

    def get_knowledge_retriever(self):
        """Lazy load the knowledge retriever"""
        if self._knowledge_retriever is None:
            try:
                from rag.retriever import KnowledgeRetriever
                self._knowledge_retriever = KnowledgeRetriever()
            except ImportError:
                print(f"⚠️  RAG system not available for {self.name}")
                self._knowledge_retriever = False
        return self._knowledge_retriever

    def retrieve_knowledge(self, query: str, use_rag: bool = True) -> str:
        """Retrieve relevant knowledge from agent's domain"""
        if not use_rag or not self.knowledge_domain:
            return ""
        
        retriever = self.get_knowledge_retriever()
        if not retriever:
            return ""
        
        try:
            # Create search query combining topic and agent's expertise
            search_query = f"{query} {self.expertise}" if self.expertise else query
            
            # Retrieve knowledge from agent's domain
            knowledge_context = retriever.get_context_string(
                domain=self.knowledge_domain,
                query=search_query,
                top_k=2  # Limit to 2 most relevant pieces
            )
            
            if knowledge_context:
                return f"\n[📚 Knowledge from {self.knowledge_domain} domain:]\n{knowledge_context}"
            
        except Exception as e:
            print(f"⚠️  Knowledge retrieval failed for {self.name}: {e}")
        
        return ""

    def build_prompt(self, topic, context, round_number, stage, word_limits=None, use_rag=True):
        """Build prompt with optional RAG knowledge enhancement"""
        # Core prompt structure
        lines = [
            f"You are {self.name}, {self.persona} {self.role}.",
            f"Topic: {topic}",
        ]
        
        # Add expertise/style if provided
        if self.expertise:
            lines.append(f"Expertise: {self.expertise}")
        if self.style:
            lines.append(f"Style: {self.style}")
        
        # Add RAG knowledge if enabled
        if use_rag:
            rag_knowledge = self.retrieve_knowledge(f"{topic} {stage}", use_rag)
            if rag_knowledge:
                lines.append(rag_knowledge)
        
        # Stage-specific instructions
        if word_limits:
            # With length limits
            word_limit = word_limits.get(stage, {"words": 100})["words"]
            stage_instructions = {
                "opening": f"Give your opening position in EXACTLY {word_limit} words or fewer.",
                "rebuttal": f"Rebut opponents' arguments in EXACTLY {word_limit} words or fewer.",
                "closing": f"Make your final closing argument in EXACTLY {word_limit} words or fewer."
            }
            lines.append(stage_instructions.get(stage, f"Respond in EXACTLY {word_limit} words or fewer."))
        else:
            # Without length limits - natural responses
            stage_instructions = {
                "opening": "Give your opening position on this topic.",
                "rebuttal": "Respond to the previous arguments while presenting your perspective.",
                "closing": "Make your final closing argument."
            }
            lines.append(stage_instructions.get(stage, "Continue the debate."))
        
        # Add conversation context if available
        if context:
            lines.append(f"Previous arguments:\n{context}")
        
        # Instructions about using knowledge
        if use_rag and self.knowledge_domain:
            lines.append("\nUse the provided knowledge to support your arguments with specific facts and sources.")
        
        # Length enforcement only if limits are set
        if word_limits:
            word_limit = word_limits.get(stage, {"words": 100})["words"]
            lines.extend([
                "",
                f"CRITICAL: Your response MUST be {word_limit} words or fewer.",
                "Be concise, impactful, and stay within the limit.",
                "",
                "Your response:"
            ])
        else:
            lines.extend([
                "",
                "Your response:"
            ])
        
        return "\n".join(lines)

    def respond(self, topic, context, round_number, stage, word_limits=None, use_rag=True):
        """Generate response with optional RAG enhancement"""
        prompt = self.build_prompt(topic, context, round_number, stage, word_limits, use_rag)
        config = get_creative_config(stage, word_limits)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text.strip()
        except Exception as e:
            return f"[Error: {e}]"

    def get_agent_info(self):
        """Get detailed agent information including RAG status"""
        return {
            "name": self.name,
            "role": self.role,
            "expertise": self.expertise,
            "knowledge_domain": self.knowledge_domain,
            "rag_enabled": self.knowledge_domain is not None
        }

    def __str__(self):
        domain_info = f" [{self.knowledge_domain}]" if self.knowledge_domain else ""
        return f"{self.name} ({self.role}){domain_info}"
