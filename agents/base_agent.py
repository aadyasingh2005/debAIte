import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define different configs for different use cases
CREATIVE_CONFIG = genai.GenerationConfig(
    temperature=0.7,      # More creative for debate responses
    max_output_tokens=300,
    top_p=0.95,
    top_k=40
)

DETERMINISTIC_CONFIG = genai.GenerationConfig(
    temperature=0.0,      # Deterministic for summaries
    max_output_tokens=300,
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

    def build_prompt(self, topic, context, round_number, stage):
        stage_map = {
            "opening":  "Give your opening (≤150 words).",
            "rebuttal": "Rebut opponents (≤150 words).",
            "closing":  "Closing statement (≤150 words).",
        }
        lines = [
            f"You are {self.name}, {self.persona} {self.role}.",
            f"Topic: {topic}",
            stage_map.get(stage, "Respond (≤150 words)."),
        ]
        if self.expertise:
            lines.insert(1, f"Expertise: {self.expertise}")
        if self.style:
            lines.insert(2, f"Speaking style: {self.style}")
        if context:
            lines.append(f"Previous:\n{context}")
        lines.append("Response:")
        return "\n".join(lines)

    def respond(self, topic, context, round_number, stage):
        prompt = self.build_prompt(topic, context, round_number, stage)
        try:
            # Use creative config for debate responses
            resp = self.model.generate_content(
                prompt,
                generation_config=CREATIVE_CONFIG  # 0.7 temperature
            )
            return resp.text.strip()
        except Exception as e:
            return f"[Error: {e}]"

    def __str__(self):
        return f"{self.name} ({self.role})"
