from agents.conversation_manager import ConversationManager
import time

class DebateController:
    def __init__(self, agents, topic):
        self.agents = agents
        self.topic = topic
        self.conversation_manager = ConversationManager()
        self.max_rounds = 3  # Configurable
        
    def run_structured_debate(self):
        """Run a complete structured debate"""
        print(f"🎯 Starting Debate: {self.topic}")
        print("=" * 60)
        
        # Initialize debate
        self.conversation_manager.start_debate(self.topic, self.agents)
        
        # Round 1: Opening Statements
        self._run_opening_statements()
        
        # Round 2-N: Rebuttal Rounds
        for round_num in range(2, self.max_rounds):
            self._run_rebuttal_round(round_num)
        
        # Final Round: Closing Arguments
        self._run_closing_arguments()
        
        # Debate Summary
        self._display_debate_summary()
        
        return self.conversation_manager.get_full_conversation()
    
    def _run_opening_statements(self):
        """Round 1: Each agent gives opening statement"""
        print("\n🔥 ROUND 1: OPENING STATEMENTS")
        print("-" * 40)
        
        self.conversation_manager.advance_round()
        
        for agent in self.agents:
            print(f"\n{agent.name} ({agent.role}):")
            
            response = agent.respond(
                topic=self.topic,
                context="",  # No context for opening statements
                round_number=1,
                debate_stage="opening"
            )
            
            print(response)
            self.conversation_manager.add_message(agent.name, response)
            time.sleep(1)  # Small delay for readability
    
    def _run_rebuttal_round(self, round_number):
        """Rebuttal rounds: Agents respond to each other"""
        print(f"\n🥊 ROUND {round_number}: REBUTTALS")
        print("-" * 40)
        
        self.conversation_manager.advance_round()
        
        for agent in self.agents:
            print(f"\n{agent.name} ({agent.role}):")
            
            # Get context of what others have said
            context = self.conversation_manager.get_context_for_agent(agent.name)
            
            response = agent.respond(
                topic=self.topic,
                context=context,
                round_number=round_number,
                debate_stage="rebuttal"
            )
            
            print(response)
            self.conversation_manager.add_message(agent.name, response)
            time.sleep(1)
    
    def _run_closing_arguments(self):
        """Final round: Closing arguments"""
        print(f"\n🎬 FINAL ROUND: CLOSING ARGUMENTS")
        print("-" * 40)
        
        self.conversation_manager.advance_round()
        
        for agent in self.agents:
            print(f"\n{agent.name} ({agent.role}) - Final Statement:")
            
            # Get full context for closing
            context = self.conversation_manager.get_context_for_agent(agent.name, last_n_messages=8)
            
            response = agent.respond(
                topic=self.topic,
                context=context,
                round_number=self.conversation_manager.round_number,
                debate_stage="closing"
            )
            
            print(response)
            self.conversation_manager.add_message(agent.name, response)
            time.sleep(1)
    
    def _display_debate_summary(self):
        """Show debate statistics and summary"""
        print("\n" + "=" * 60)
        print("📊 DEBATE SUMMARY")
        print("=" * 60)
        
        print(f"Topic: {self.topic}")
        print(f"Total Rounds: {self.conversation_manager.round_number}")
        print(f"Total Messages: {len([h for h in self.conversation_manager.history if h['type'] != 'system'])}")
        
        print("\nParticipant Statistics:")
        for agent in self.agents:
            stats = agent.get_agent_stats()
            print(f"- {stats['name']}: {stats['messages_sent']} messages")
        
        # Export option
        filename = self.conversation_manager.export_debate()
        print(f"\n💾 Debate exported to: {filename}")
