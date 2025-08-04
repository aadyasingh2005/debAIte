import json
from datetime import datetime

class ConversationManager:
    def __init__(self):
        self.history = []
        self.round_number = 0
        self.debate_topic = ""
    
    def start_debate(self, topic, participants):
        """Initialize a new debate session"""
        self.debate_topic = topic
        self.history = []
        self.round_number = 0
        self.participants = [agent.name for agent in participants]
        
        # Log debate start
        self.add_system_message(f"Debate started: {topic}")
        self.add_system_message(f"Participants: {', '.join(self.participants)}")
    
    def add_message(self, agent_name, message, message_type="response"):
        """Add a message to conversation history"""
        entry = {
            "round": self.round_number,
            "agent": agent_name,
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(entry)
    
    def add_system_message(self, message):
        """Add system/admin message"""
        self.add_message("SYSTEM", message, "system")
    
    def get_context_for_agent(self, agent_name, last_n_messages=4):
        """Get conversation context for an agent (excluding system messages)"""
        # Filter out system messages and get recent conversation
        conversation_messages = [
            h for h in self.history 
            if h["type"] != "system"
        ]
        
        # Get last N messages for context
        recent_messages = conversation_messages[-last_n_messages:]
        
        # Format as readable context
        context_lines = []
        for msg in recent_messages:
            if msg["agent"] != agent_name:  # Don't include agent's own messages in context
                context_lines.append(f"{msg['agent']}: {msg['message']}")
        
        return "\n".join(context_lines)
    
    def get_full_conversation(self):
        """Get the full conversation history"""
        return self.history
    
    def summarize_conversation(self):
        """Create a summary of the conversation so far"""
        conversation_messages = [
            h for h in self.history 
            if h["type"] != "system"
        ]
        
        if len(conversation_messages) <= 2:
            return "Debate just started."
        
        # Simple summarization (you could enhance this with LLM)
        participants = set(msg["agent"] for msg in conversation_messages)
        total_messages = len(conversation_messages)
        
        return f"Round {self.round_number}: {total_messages} messages exchanged between {', '.join(participants)}."
    
    def advance_round(self):
        """Move to the next round"""
        self.round_number += 1
        self.add_system_message(f"Round {self.round_number} started")
    
    def export_debate(self, filename=None):
        """Export debate to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debate_{timestamp}.json"
        
        export_data = {
            "topic": self.debate_topic,
            "participants": self.participants,
            "total_rounds": self.round_number,
            "history": self.history
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return filename
