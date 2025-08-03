import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class DebateAgent:
    def __init__(self, name, persona, role):
        self.name = name
        self.persona = persona
        self.role = role
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def build_prompt(self, topic, context=""):
        return (
            f"You are {self.name}, a {self.persona} {self.role}.\n"
            f"Debate topic: {topic}\n"
            f"Context: {context}\n"
            f"Your response:"
        )

    def respond(self, topic, context=""):
        prompt = self.build_prompt(topic, context)
        response = self.model.generate_content(prompt)
        return response.text.strip()
