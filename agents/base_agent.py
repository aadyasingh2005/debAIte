import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Default creative config (no length limits)
CREATIVE_CONFIG = genai.GenerationConfig(
    temperature=0.7,
    max_output_tokens=500,  # Generous default
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
    def __init__(self, name, persona, role, expertise="", style=""):
        self.name = name
        self.persona = persona
        self.role = role
        self.expertise = expertise
        self.style = style
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def build_prompt(self, topic, context, round_number, stage, word_limits=None):
        """Build prompt with optional length enforcement"""
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
        
        # Add context if available
        if context:
            lines.append(f"Previous arguments:\n{context}")
        
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

    def respond(self, topic, context, round_number, stage, word_limits=None):
        """Generate response with optional length limits"""
        prompt = self.build_prompt(topic, context, round_number, stage, word_limits)
        config = get_creative_config(stage, word_limits)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text.strip()
        except Exception as e:
            return f"[Error: {e}]"

    def __str__(self):
        return f"{self.name} ({self.role})"
