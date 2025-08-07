import numpy as np
from sentence_transformers import SentenceTransformer
import re
import random
from typing import Dict, Tuple

class HybridDomainController:
    """Combines prompt guidance with technical validation for domain control"""
    
    def __init__(self):
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.similarity_threshold = 0.3  # Lower threshold - only flag significant drift
        
        # Domain anchor texts that define expertise areas
        self.domain_anchors = {
            "medical": "clinical diagnosis patient treatment healthcare medical research evidence-based medicine patient safety FDA clinical trials therapeutic interventions diagnostic accuracy medical ethics",
            
            "tech": "business technology startup market ROI development scalability artificial intelligence software engineering venture capital product development market analysis business strategy",
            
            "ethics": "moral principles fairness justice social responsibility values ethical frameworks human rights societal impact philosophical analysis moral reasoning ethical dilemmas",
            
            "legal": "law regulation constitutional rights legal precedent court decisions policy compliance regulatory framework legal analysis jurisprudence statutory interpretation",
            
            "economics": "economic analysis market dynamics financial impact cost-benefit analysis economic policy fiscal analysis monetary policy economic indicators market trends"
        }
        
        # Pre-compute anchor embeddings for efficiency
        self.anchor_embeddings = {
            domain: self.embedder.encode(anchor_text)
            for domain, anchor_text in self.domain_anchors.items()
        }
        
        print("✅ Hybrid Domain Controller initialized with semantic embeddings")
    
    def get_enhanced_prompt_guidance(self, agent):
        """Get improved prompt guidance for natural expert behavior"""
        
        domain_guidance = {
            "medical": """
PROFESSIONAL APPROACH as a Medical Expert:
- Lead with clinical evidence, patient safety, and healthcare outcomes
- Draw from medical research, FDA guidelines, and clinical best practices  
- Acknowledge when topics require business, legal, or technical expertise beyond clinical practice
- Frame non-medical aspects through the lens of patient care and healthcare delivery
- Be confident about medical facts, thoughtful about interdisciplinary implications
            """,
            
            "tech": """
PROFESSIONAL APPROACH as a Technology Expert:
- Lead with technical feasibility, business viability, and market analysis
- Draw from startup experience, product development, and AI implementation
- Acknowledge when topics require medical, legal, or ethical expertise beyond business/tech
- Frame non-technical aspects through the lens of product impact and market dynamics
- Be confident about tech/business facts, thoughtful about societal implications
            """,
            
            "ethics": """
PROFESSIONAL APPROACH as an Ethics Expert:
- Lead with moral principles, philosophical frameworks, and societal impact
- Draw from ethical theory, case studies, and philosophical analysis
- Acknowledge when topics require technical, medical, or legal expertise beyond ethics
- Frame technical/business aspects through the lens of moral implications and social justice
- Be confident about ethical principles, thoughtful about practical implementation
            """,
            
            "legal": """
PROFESSIONAL APPROACH as a Legal Expert:
- Lead with regulatory frameworks, legal precedents, and constitutional analysis
- Draw from case law, statutory interpretation, and policy analysis
- Acknowledge when topics require technical, medical, or business expertise beyond law
- Frame other aspects through the lens of legal compliance and rights protection
- Be confident about legal principles, thoughtful about practical enforcement
            """,
            
            "economics": """
PROFESSIONAL APPROACH as an Economics Expert:
- Lead with economic analysis, market dynamics, and financial implications
- Draw from economic theory, market data, and policy impact studies
- Acknowledge when topics require technical, medical, or legal expertise beyond economics
- Frame other aspects through the lens of economic efficiency and market outcomes
- Be confident about economic principles, thoughtful about social implications
            """
        }
        
        return domain_guidance.get(agent.knowledge_domain, "")
    
    def calculate_domain_alignment(self, response: str, agent_domain: str) -> Dict[str, float]:
        """Calculate semantic similarity between response and all domain anchors"""
        
        response_embedding = self.embedder.encode(response)
        
        similarities = {}
        for domain, anchor_embedding in self.anchor_embeddings.items():
            # Cosine similarity calculation
            similarity = np.dot(response_embedding, anchor_embedding) / (
                np.linalg.norm(response_embedding) * np.linalg.norm(anchor_embedding)
            )
            similarities[domain] = float(similarity)
        
        return similarities
    
    def assess_domain_drift(self, response: str, agent_domain: str) -> Tuple[bool, Dict]:
        """Assess if response has drifted from agent's domain expertise - IMPROVED VERSION"""
        
        similarities = self.calculate_domain_alignment(response, agent_domain)
        
        agent_domain_similarity = similarities[agent_domain]
        other_similarities = {k: v for k, v in similarities.items() if k != agent_domain}
        max_other_domain = max(other_similarities.keys(), key=lambda k: other_similarities[k])
        max_other_similarity = other_similarities[max_other_domain]
        
        # ✅ IMPROVED LOGIC: Only flag significant drift
        significant_drift = (
            agent_domain_similarity < 0.25 and  # Very low threshold - only terrible responses
            max_other_similarity > agent_domain_similarity + 0.3  # Other domain must be much higher
        )
        
        # ✅ CHECK: Don't flag if response already has domain framing
        has_domain_framing = self._has_existing_qualifier(response, agent_domain)
        
        drift_detected = significant_drift and not has_domain_framing
        
        analysis = {
            'agent_domain_similarity': agent_domain_similarity,
            'max_other_domain': max_other_domain,
            'max_other_similarity': max_other_similarity,
            'drift_detected': drift_detected,
            'confidence_in_domain': agent_domain_similarity > 0.2,
            'has_existing_qualifier': has_domain_framing,
            'significant_drift': significant_drift,
            'all_similarities': similarities
        }
        
        return drift_detected, analysis
    
    def _has_existing_qualifier(self, response: str, agent_domain: str) -> bool:
        """Check if response already has appropriate domain framing"""
        
        response_lower = response.lower().strip()
        
        # Check for existing domain qualifiers
        existing_qualifiers = [
            "from my", "in my", "as a", "from a", "speaking as",
            "from the perspective", "in the context of", "considering",
            "based on my", "drawing from", "given my"
        ]
        
        # Check for domain-specific phrases that show awareness
        domain_phrases = {
            "medical": ["clinical", "patient", "medical", "healthcare", "diagnosis", "treatment", "therapeutic"],
            "tech": ["business", "technical", "market", "development", "startup", "ROI", "scalability"],
            "ethics": ["ethical", "moral", "philosophical", "values", "justice", "principles"],
            "legal": ["legal", "regulatory", "constitutional", "policy", "compliance", "precedent"],
            "economics": ["economic", "financial", "market", "cost", "policy", "fiscal"]
        }
        
        # If response starts with qualifier, it's already framed
        if any(response_lower.startswith(qualifier) for qualifier in existing_qualifiers):
            return True
        
        # If response contains domain-specific professional language, it's appropriately framed
        if agent_domain in domain_phrases:
            domain_words = domain_phrases[agent_domain]
            domain_word_count = sum(1 for word in domain_words if word in response_lower)
            if domain_word_count >= 3:  # Contains multiple domain words
                return True
        
        return False
    
    def apply_technical_correction(self, response: str, agent_domain: str, analysis: Dict) -> str:
        """Apply gentle technical correction only when truly needed"""
        
        if not analysis['drift_detected']:
            return response  # No correction needed
        
        # ✅ VARIED, NATURAL QUALIFIERS: Rotate to avoid repetition
        gentle_corrections = {
            "medical": [
                "From a clinical standpoint, ",
                "In healthcare terms, ",
                "Medically speaking, ",
                "From the medical perspective, "
            ],
            "tech": [
                "From a technical angle, ",
                "Business-wise, ",
                "From the tech perspective, ",
                "Looking at this technically, "
            ],
            "ethics": [
                "From an ethical standpoint, ",
                "Morally speaking, ",
                "From a values perspective, ",
                "Ethically, "
            ],
            "legal": [
                "From a legal perspective, ",
                "Regulatory-wise, ",
                "From the policy standpoint, ",
                "Legally speaking, "
            ],
            "economics": [
                "From an economic perspective, ",
                "Financially speaking, ",
                "From a market standpoint, ",
                "Economically, "
            ]
        }
        
        qualifiers = gentle_corrections.get(agent_domain, ["From my professional perspective, "])
        qualifier = random.choice(qualifiers)
        
        # Add qualifier naturally
        if not response.lower().startswith(('from', 'in ', 'as ', 'while', 'however', 'although')):
            return f"{qualifier}{response[0].lower()}{response[1:]}"
        
        return response
    
    def get_transparency_info(self, analysis: Dict) -> str:
        """Generate transparency information for users/developers"""
        
        if analysis['drift_detected']:
            return f"⚠️ Domain alignment: {analysis['agent_domain_similarity']:.2f} (threshold: {self.similarity_threshold}). Strongest signal from {analysis['max_other_domain']} ({analysis['max_other_similarity']:.2f}). Applied gentle correction."
        else:
            return f"✅ Good domain alignment: {analysis['agent_domain_similarity']:.2f}. No intervention needed."
