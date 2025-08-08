import time
from datetime import datetime
from typing import List, Dict, Any
from agents.base_agent import DebateAgent

class UserVsAIController:
    """Controller for user vs AI debates"""
    
    def __init__(self, ai_agents: List[DebateAgent], topic: str, user_goes_first: bool = True, 
                 use_length_limits: bool = False, word_limits: Dict = None, use_rag: bool = True):
        self.ai_agents = ai_agents
        self.topic = topic
        self.user_goes_first = user_goes_first
        self.use_length_limits = use_length_limits
        self.word_limits = word_limits or {}
        self.use_rag = use_rag
        
        self.debate_history = []
        self.current_round = 0
        self.max_rounds = 4  # Opening, 2 rebuttals, closing
        
    def run(self):
        """Run the user vs AI debate"""
        print(f"\n🗣️  USER vs AI DEBATE")
        print("=" * 60)
        print(f"Topic: {self.topic}")
        print(f"AI Opponents: {', '.join([agent.name for agent in self.ai_agents])}")
        print(f"Order: {'User first' if self.user_goes_first else 'AI first'}")
        
        if self.use_length_limits:
            print(f"Word limits enabled: {self.word_limits}")
        
        print("\nInstructions:")
        print("• Type your argument when prompted")
        print("• Type 'skip' to skip your turn")
        print("• Type 'quit' to end debate early")
        print("• Press Enter on empty line when done typing")
        
        input("\nPress Enter to start the debate...")
        
        # Run debate rounds
        for round_num in range(self.max_rounds):
            self.current_round = round_num
            stage = self._get_stage(round_num)
            
            print(f"\n{'='*20} ROUND {round_num + 1}: {stage.upper()} {'='*20}")
            
            if self.user_goes_first:
                self._handle_user_turn(stage)
                self._handle_ai_turns(stage)
            else:
                self._handle_ai_turns(stage)
                self._handle_user_turn(stage)
        
        # Show debate summary
        self._show_debate_summary()
    
    def _get_stage(self, round_num: int) -> str:
        """Get debate stage name"""
        stages = ["opening", "rebuttal", "rebuttal", "closing"]
        return stages[round_num] if round_num < len(stages) else "closing"
    
    def _handle_user_turn(self, stage: str):
        """Handle user's turn to speak"""
        print(f"\n👤 YOUR TURN ({stage})")
        
        if self.use_length_limits and stage in self.word_limits:
            word_limit = self.word_limits[stage]['words']
            print(f"📏 Word limit: {word_limit} words")
        
        print("Enter your argument (press Enter twice to finish):")
        print("-" * 40)
        
        # Multi-line input
        user_response = ""
        empty_lines = 0
        
        while True:
            line = input()
            
            if line.strip() == "":
                empty_lines += 1
                if empty_lines >= 2 or user_response.strip() == "":
                    break
                user_response += "\n"
            else:
                empty_lines = 0
                user_response += line + "\n"
        
        user_response = user_response.strip()
        
        # Handle special commands
        if user_response.lower() in ['quit', 'exit']:
            print("🏃 User quit the debate.")
            return False
        
        if user_response.lower() == 'skip':
            user_response = "[User skipped this round]"
        
        if not user_response:
            user_response = "[No response provided]"
        
        # Check word limit
        if self.use_length_limits and stage in self.word_limits:
            word_count = len(user_response.split())
            word_limit = self.word_limits[stage]['words']
            if word_count > word_limit:
                print(f"⚠️ Your response ({word_count} words) exceeds the limit ({word_limit} words).")
                print("Please shorten your response.")
                return self._handle_user_turn(stage)  # Retry
        
        # Store user response
        self.debate_history.append({
            'round': self.current_round + 1,
            'stage': stage,
            'speaker': 'User',
            'role': 'human debater',
            'response': user_response,
            'timestamp': datetime.now(),
            'word_count': len(user_response.split())
        })
        
        print(f"✅ Your {stage} recorded ({len(user_response.split())} words)")
        return True
    
    def _handle_ai_turns(self, stage: str):
        """Handle AI agents' turns"""
        print(f"\n🤖 AI RESPONSES ({stage})")
        
        context = self._build_context()
        
        for i, agent in enumerate(self.ai_agents):
            print(f"\n[{i+1}/{len(self.ai_agents)}] {agent.name} is responding...")
            
            try:
                ai_response = agent.respond(
                    topic=self.topic,
                    context=context,
                    round_number=self.current_round + 1,
                    stage=stage,
                    word_limits=self.word_limits if self.use_length_limits else None,
                    use_rag=self.use_rag
                )
                
                # Store AI response
                self.debate_history.append({
                    'round': self.current_round + 1,
                    'stage': stage,
                    'speaker': agent.name,
                    'role': agent.role,
                    'response': ai_response,
                    'timestamp': datetime.now(),
                    'domain': agent.knowledge_domain,
                    'word_count': len(ai_response.split())
                })
                
                # Display AI response
                print(f"\n🎭 {agent.name} ({agent.role}):")
                print("-" * 40)
                print(ai_response)
                
                # Show domain analysis if available
                if hasattr(agent, 'get_domain_analysis'):
                    analysis = agent.get_domain_analysis()
                    if analysis:
                        similarity = analysis.get('agent_domain_similarity', 0)
                        drift = analysis.get('drift_detected', False)
                        print(f"📊 Domain: {agent.knowledge_domain} | Similarity: {similarity:.2f} | Drift: {drift}")
                
                time.sleep(1)  # Brief pause for readability
                
            except Exception as e:
                error_msg = f"[Error: {agent.name} failed to respond - {e}]"
                print(f"❌ {error_msg}")
                
                self.debate_history.append({
                    'round': self.current_round + 1,
                    'stage': stage,
                    'speaker': agent.name,
                    'role': agent.role,
                    'response': error_msg,
                    'timestamp': datetime.now(),
                    'domain': agent.knowledge_domain,
                    'word_count': 0
                })
    
    def _build_context(self) -> str:
        """Build context from recent debate history"""
        if not self.debate_history:
            return ""
        
        # Get last few exchanges for context (max 6 entries)
        recent_history = self.debate_history[-6:]
        
        context_parts = []
        for entry in recent_history:
            speaker = entry['speaker']
            response = entry['response'][:200] + ("..." if len(entry['response']) > 200 else "")
            context_parts.append(f"{speaker}: {response}")
        
        return "\n".join(context_parts)
    
    def _show_debate_summary(self):
        """Show final debate summary"""
        print(f"\n🏁 DEBATE COMPLETED")
        print("=" * 60)
        
        # Basic stats
        user_responses = [entry for entry in self.debate_history if entry['speaker'] == 'User']
        ai_responses = [entry for entry in self.debate_history if entry['speaker'] != 'User']
        
        user_word_count = sum(entry['word_count'] for entry in user_responses)
        ai_word_count = sum(entry['word_count'] for entry in ai_responses)
        
        print(f"📊 DEBATE STATISTICS:")
        print(f"   Total rounds: {self.max_rounds}")
        print(f"   User responses: {len(user_responses)} ({user_word_count} words)")
        print(f"   AI responses: {len(ai_responses)} ({ai_word_count} words)")
        print(f"   Total exchanges: {len(self.debate_history)}")
        
        # Show full debate history
        print(f"\n📜 FULL DEBATE TRANSCRIPT:")
        print("=" * 60)
        
        current_round = 0
        for entry in self.debate_history:
            if entry['round'] != current_round:
                current_round = entry['round']
                print(f"\n🗣️ ROUND {current_round}: {entry['stage'].upper()}")
                print("-" * 40)
            
            speaker_icon = "👤" if entry['speaker'] == 'User' else "🤖"
            print(f"\n{speaker_icon} {entry['speaker']}:")
            print(entry['response'])
            print(f"   ⏱️ {entry['timestamp'].strftime('%H:%M:%S')} | {entry['word_count']} words")
        
        print(f"\n🎉 Thank you for debating! The transcript shows all exchanges.")
