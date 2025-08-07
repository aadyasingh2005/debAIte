import os
import re
from dotenv import load_dotenv
from agents.domain_controller import HybridDomainController

load_dotenv()

def get_creative_config(stage=None, word_limits=None):
    """Get generation config with optional length limits"""
    base_config = {
        'temperature': 0.7,
        'max_tokens': 500,
        'top_p': 0.95,
        'top_k': 40
    }
    
    if word_limits and stage in word_limits:
        base_config['max_tokens'] = word_limits[stage]['tokens']
    
    return base_config

class DebateAgent:
    def __init__(self, name, persona, role, expertise="", style="", knowledge_domain=None):
        self.name = name
        self.persona = persona
        self.role = role
        self.expertise = expertise
        self.style = style
        self.knowledge_domain = knowledge_domain or self._map_role_to_domain()
        
        # Don't create any model here - will be set later
        self.model_provider = None
        self._knowledge_retriever = None
        
        # Initialize hybrid controller (shared across agents)
        if not hasattr(DebateAgent, '_domain_controller'):
            DebateAgent._domain_controller = HybridDomainController()
        
        self.domain_controller = DebateAgent._domain_controller

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
            "privacy rights advocate": "legal",
            "privacy advocate": "legal",
            "advocate": "legal",
            
            "economist": "economics",
            "business analyst": "economics",
            "financial analyst": "economics",
            "market researcher": "economics"
        }
        
        role_lower = self.role.lower()
        for key, domain in role_to_domain.items():
            if key in role_lower:
                return domain
        
        return None

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
            # Create more specific search queries
            search_queries = [
                query,  # Original query
                f"{query} {self.role}",  # Add role context
                f"{self.expertise} {query}",  # Add expertise context
            ]
            
            all_results = []
            for search_query in search_queries:
                results = retriever.retrieve_knowledge(self.knowledge_domain, search_query, top_k=1)
                all_results.extend(results)
            
            # Remove duplicates and get top results
            unique_results = []
            seen_content = set()
            for result in all_results:
                content_key = result['content'][:100]  # First 100 chars as key
                if content_key not in seen_content:
                    unique_results.append(result)
                    seen_content.add(content_key)
            
            if unique_results:
                context_parts = [f"[📚 Knowledge from {self.knowledge_domain} domain:]"]
                for i, result in enumerate(unique_results[:2], 1):  # Top 2 results
                    context_parts.append(f"{i}. {result['content'][:300]}...")
                    context_parts.append(f"   Source: {result['source']}")
                return "\n".join(context_parts)
                
        except Exception as e:
            print(f"⚠️  Knowledge retrieval failed for {self.name}: {e}")
        
        return ""

    def build_prompt(self, topic, context, round_number, stage, word_limits=None, use_rag=True):
        """Build prompt with enhanced domain guidance"""
        lines = [
            f"You are {self.name}, {self.persona} {self.role}.",
            f"Topic: {topic}",
        ]
        
        if self.expertise:
            lines.append(f"Your expertise: {self.expertise}")
        if self.style:
            lines.append(f"Your speaking style: {self.style}")
        
        # Add RAG knowledge if available
        if use_rag and self.knowledge_domain:
            rag_knowledge = self.retrieve_knowledge(f"{topic} {stage}", use_rag)
            if rag_knowledge:
                lines.append("\n" + "="*50)
                lines.append("YOUR DOMAIN KNOWLEDGE BASE:")
                lines.append(rag_knowledge)
                lines.append("="*50)
        
        # Add enhanced domain guidance
        domain_guidance = self.domain_controller.get_enhanced_prompt_guidance(self)
        if domain_guidance:
            lines.append(f"\n{domain_guidance}")
        
        # Stage-specific instructions
        if word_limits:
            word_limit = word_limits.get(stage, {"words": 100})["words"]
            stage_instructions = {
                "opening": f"Provide your professional opening perspective in {word_limit} words or fewer.",
                "rebuttal": f"Respond to previous arguments from your expertise in {word_limit} words or fewer.",
                "closing": f"Make your final professional argument in {word_limit} words or fewer."
            }
        else:
            stage_instructions = {
                "opening": "Provide your professional opening perspective on this topic.",
                "rebuttal": "Respond to previous arguments from your area of expertise.",
                "closing": "Make your final professional argument."
            }
        
        lines.append(stage_instructions.get(stage, "Provide your professional perspective on this topic."))
        
        if context:
            lines.append(f"\nPrevious discussion:\n{context}")
        
        lines.extend([
            "",
            "RESPONSE GUIDELINES:",
            "- Speak naturally as a professional expert in your field",
            "- Lead with your domain expertise and evidence",
            "- Acknowledge limitations when discussing other fields", 
            "- Provide thoughtful insights while staying grounded in your expertise",
            "- Don't say 'As [Your Name]' - just give your professional opinion directly",
            "- Be conversational, not overly academic or formal",
            "- Get straight to the point and sound human",
            "",
            "Your response:"
        ])
        
        return "\n".join(lines)

    def clean_response(self, response: str) -> str:
        """Clean up overly formal or robotic responses"""
        # Remove "As [Name]" starts
        response = re.sub(r'^As (Dr\.|Prof\.|Attorney |Ms\.|Mr\.)?[^,]+,?\s*', '', response, flags=re.IGNORECASE)
        
        # Remove overly formal introductions
        formal_starters = [
            r"my stance on",
            r"my perspective aligns with",
            r"from my viewpoint as",
            r"in my capacity as",
            r"speaking as a"
        ]
        
        for pattern in formal_starters:
            response = re.sub(r'^[^.]*' + pattern + r'[^.]*\.\s*', '', response, flags=re.IGNORECASE)
        
        # Replace overly academic language
        replacements = {
            r"herein": "here",
            r"furthermore": "also",
            r"nonetheless": "however", 
            r"wherein": "where",
            r"thereby": "so",
            r"thus": "so",
            r"hence": "so"
        }
        
        for formal, casual in replacements.items():
            response = re.sub(formal, casual, response, flags=re.IGNORECASE)
        
        return response.strip()

    def respond(self, topic, context, round_number, stage, word_limits=None, use_rag=True):
        """Generate domain-controlled response using hybrid approach"""
        if not self.model_provider:
            return f"[Error: No model provider set for {self.name}]"
        
        # 1. Generate response with enhanced prompts
        prompt = self.build_prompt(topic, context, round_number, stage, word_limits, use_rag)
        config = get_creative_config(stage, word_limits)
        
        try:
            initial_response = self.model_provider.generate_content(prompt, config)
            
            # 2. Apply technical validation and correction
            drift_detected, analysis = self.domain_controller.assess_domain_drift(
                initial_response, self.knowledge_domain
            )
            
            final_response = self.domain_controller.apply_technical_correction(
                initial_response, self.knowledge_domain, analysis
            )
            
            # 3. Clean up the response
            cleaned_response = self.clean_response(final_response)
            
            # 4. Store analysis for debugging/transparency
            self.last_domain_analysis = analysis
            
            return cleaned_response
            
        except Exception as e:
            return f"[Error with {self.model_provider.get_name()}: {e}]"

    def get_domain_analysis(self):
        """Get the domain analysis from the last response for transparency"""
        return getattr(self, 'last_domain_analysis', {})

    def get_agent_info(self):
        """Get detailed agent information including model provider"""
        provider_name = self.model_provider.get_name() if self.model_provider else "None"
        return {
            "name": self.name,
            "role": self.role,
            "expertise": self.expertise,
            "knowledge_domain": self.knowledge_domain,
            "model_provider": provider_name,
            "rag_enabled": self.knowledge_domain is not None
        }

    def __str__(self):
        domain_info = f" [{self.knowledge_domain}]" if self.knowledge_domain else ""
        provider_info = f" ({self.model_provider.get_name().split()[0]})" if self.model_provider else ""
        return f"{self.name} ({self.role}){domain_info}{provider_info}"
