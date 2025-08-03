import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

class DebateAgent:
    def __init__(self, name, persona, role):
        self.name = name
        self.persona = persona
        self.role = role

    def build_prompt(self, topic, context=""):
        return (
            f"You are {self.name}, {self.persona} {self.role}.\n"
            f"Debate topic: {topic}\n"
            f"Context: {context}\n"
            f"Your response:"
        )

    def respond(self, topic, context=""):
        prompt = self.build_prompt(topic, context)
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return completion.choices[0].message["content"].strip()
