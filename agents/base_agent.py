import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class DebateAgent:
    def __init__(self, name, persona, role, expertise_area="", speaking_style=""):
        self.name = name
        self.persona = persona
        self.role = role
        self.expertise_area = expertise_area
        self.speaking_style = speaking_style
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.message_count = 0  # Track how many times this agent has spoken

    def build_prompt(self, topic, context="", round_number=1, debate_stage="ongoing"):
        """Build contextual prompt based on debate stage and history"""
        
        prompt_parts = [
            f"You are {self.name}, a {self.persona} {self.role}."
        ]
        
        if self.expertise_area:
            prompt_parts.append(f"Your expertise: {self.expertise_area}")
        
        if self.speaking_style:
            prompt_parts.append(f"Your speaking style: {self.speaking_style}")
        
        # Add debate context
        prompt_parts.append(f"DEBATE TOPIC: {topic}")
        prompt_parts.append(f"Current Round: {round_number}")
        
        # Stage-specific instructions
        if debate_stage == "opening":
            prompt_parts.append("This is your OPENING STATEMENT. Present your main position clearly.")
        elif debate_stage == "rebuttal":
            prompt_parts.append("This is a REBUTTAL round. Address the arguments made by other participants.")
        elif debate_stage == "closing":
            prompt_parts.append("This is your CLOSING ARGUMENT. Summarize your position and make your final case.")
        else:
            prompt_parts.append("Continue the debate by responding to previous arguments.")
        
        # Add conversation history if available
        if context:
            prompt_parts.append(f"PREVIOUS ARGUMENTS:\n{context}")
            prompt_parts.append("Respond to these arguments while maintaining your position.")
        
        # Response instructions
        prompt_parts.extend([
            "Guidelines:",
            "- Keep your response focused and under 200 words",
            "- Address specific points made by others when relevant",
            "- Stay true to your character and expertise",
            "- Be respectful but persuasive",
            "",
            "Your response:"
        ])
        
        return "\n".join(prompt_parts)

    def respond(self, topic, context="", round_number=1, debate_stage="ongoing"):
        """Generate response with full context awareness"""
        prompt = self.build_prompt(topic, context, round_number, debate_stage)
        
        try:
            response = self.model.generate_content(prompt)
            self.message_count += 1
            return response.text.strip()
        except Exception as e:
            return f"[Error: {self.name} couldn't respond - {str(e)}]"

    def get_agent_stats(self):
        """Get statistics about this agent's participation"""
        return {
            "name": self.name,
            "role": self.role,
            "messages_sent": self.message_count
        }

    def __str__(self):
        return f"{self.name} ({self.role})"
