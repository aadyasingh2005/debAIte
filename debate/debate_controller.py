import time
from agents.conversation_manager import ConversationManager
from debate.context_mode import ContextMode

class DebateController:
    def __init__(self, agents, topic,
                 context_mode: ContextMode = ContextMode.HYBRID,
                 max_rounds: int = 3,
                 use_batching: bool = False,
                 use_length_limits: bool = False,
                 word_limits: dict = None,
                 use_rag: bool = False):
        
        self.agents = agents
        self.topic = topic
        self.max_rounds = max_rounds
        self.use_batching = use_batching
        self.use_length_limits = use_length_limits
        self.word_limits = word_limits if use_length_limits else None
        self.use_rag = use_rag
        self.cm = ConversationManager(mode=context_mode)
        
        # Conditionally import and initialize batch processor
        if use_batching:
            try:
                from agents.batch_processor import BatchDebateProcessor
                self.batch_processor = BatchDebateProcessor()
            except ImportError:
                print("⚠️  Batch processor not available, falling back to individual calls")
                self.use_batching = False
        
        # Check RAG availability and show agent domains
        if use_rag:
            self._check_rag_availability()
        
        # Initialize conversation
        self.cm.start_debate(topic, agents)

    def _check_rag_availability(self):
        """Check RAG system and show agent domain mappings"""
        try:
            from rag.retriever import KnowledgeRetriever
            retriever = KnowledgeRetriever()
            available_domains = retriever.available_domains()
            
            print(f"\n📚 RAG Knowledge System Status:")
            print(f"   Available domains: {', '.join(available_domains) if available_domains else 'None'}")
            
            # Show agent domain mappings
            print(f"   Agent → Domain mappings:")
            for agent in self.agents:
                domain_status = "✅" if agent.knowledge_domain in available_domains else "❌"
                domain_text = agent.knowledge_domain or "No domain"
                print(f"     • {agent.name} → {domain_text} {domain_status}")
            
            if not available_domains:
                print("   ⚠️  No knowledge bases found. Run 'python rag/indexer.py' to create them.")
                
        except ImportError:
            print("⚠️  RAG system not available")
            self.use_rag = False

    def run(self):
        """Run the complete debate with selected optimizations"""
        print(f"\n🎯 Starting Debate: {self.topic}")
        print(f"📦 Context mode: {self.cm.mode.value}")
        print(f"⚡ Optimizations:")
        print(f"   • Batching: {'✅' if self.use_batching else '❌'}")
        print(f"   • Length Limits: {'✅' if self.use_length_limits else '❌'}")
        print(f"   • RAG Knowledge: {'✅' if self.use_rag else '❌'}")
        
        if self.word_limits:
            print(f"📏 Word limits: Opening({self.word_limits['opening']['words']}), "
                  f"Rebuttal({self.word_limits['rebuttal']['words']}), "
                  f"Closing({self.word_limits['closing']['words']})")
        
        print("=" * 60)
        
        self._opening_statements()
        for r in range(2, self.max_rounds):
            self._rebuttal_round(r)
        self._closing_round()
        self._summary()

    def _opening_statements(self):
        """Round 1: Opening statements with optional optimizations"""
        print(f"\n=== ROUND 1 • Opening Statements ===")
        if self.word_limits:
            print(f"Word limit: {self.word_limits['opening']['words']} words")
        print("-" * 40)
        
        self.cm.advance_round()
        
        if self.use_batching:
            self._batch_round("opening", "")
        else:
            self._individual_round("opening", "")

    def _rebuttal_round(self, num):
        """Rebuttal rounds with optional optimizations"""
        print(f"\n=== ROUND {num} • Rebuttals ===")
        if self.word_limits:
            print(f"Word limit: {self.word_limits['rebuttal']['words']} words")
        print("-" * 40)
        
        self.cm.advance_round()
        
        if self.use_batching:
            context = self.cm.context_for("shared")
            self._batch_round("rebuttal", context)
        else:
            self._individual_round("rebuttal", None)

    def _closing_round(self):
        """Final round with optional optimizations"""
        print(f"\n=== FINAL ROUND • Closing Arguments ===")
        if self.word_limits:
            print(f"Word limit: {self.word_limits['closing']['words']} words")
        print("-" * 40)
        
        self.cm.advance_round()
        
        if self.use_batching:
            context = self.cm.context_for("shared")
            self._batch_round("closing", context)
        else:
            self._individual_round("closing", None)

    def _batch_round(self, stage: str, context: str):
        """Handle batched responses for a round"""
        # Note: Batching with RAG is complex - RAG is disabled for batch mode
        responses = self.batch_processor.batch_respond(
            self.agents, self.topic, context, stage, self.word_limits
        )
        
        for agent in self.agents:
            response = responses.get(agent.name, f"[No response from {agent.name}]")
            self.cm.add_message(agent.name, response)
            print(f"\n{agent.name}: {response}")
            time.sleep(0.3)

    def _individual_round(self, stage: str, shared_context):
        """Handle individual responses for a round"""
        for agent in self.agents:
            # Get context (individual or shared)
            if shared_context is not None:
                context = shared_context
            else:
                context = self.cm.context_for(agent.name)
            
            # Generate response with RAG if enabled
            response = agent.respond(
                topic=self.topic,
                context=context,
                round_number=1,
                stage=stage,
                word_limits=self.word_limits,
                use_rag=self.use_rag
            )
            
            self.cm.add_message(agent.name, response)
            print(f"\n{agent.name}: {response}")
            
            # Show knowledge source if RAG was used
            if self.use_rag and agent.knowledge_domain:
                print(f"   📚 Drew from {agent.knowledge_domain} knowledge base")
            
            time.sleep(0.5)

    def _summary(self):
        """Show debate statistics"""
        print("\n" + "=" * 60)
        print("📊 DEBATE SUMMARY")
        print("=" * 60)
        
        total_messages = len([h for h in self.cm.history if h['type'] != 'system'])
        
        print(f"Topic: {self.topic}")
        print(f"Total Rounds: {self.cm.round}")
        print(f"Total Messages: {total_messages}")
        print(f"Context Mode: {self.cm.mode.value}")
        
        # Show optimization stats
        print(f"Optimizations Used:")
        print(f"  • Batching: {'Yes' if self.use_batching else 'No'}")
        print(f"  • Length Limits: {'Yes' if self.use_length_limits else 'No'}")
        print(f"  • RAG Knowledge: {'Yes' if self.use_rag else 'No'}")
        
        if self.use_rag:
            print(f"Agent Knowledge Domains:")
            for agent in self.agents:
                domain = agent.knowledge_domain or "None"
                print(f"    • {agent.name}: {domain}")
        
        if self.use_batching:
            estimated_calls = self.max_rounds
            saved_calls = (len(self.agents) * self.max_rounds) - estimated_calls
            print(f"  • API Calls Saved: {saved_calls} ({saved_calls//(len(self.agents) * self.max_rounds)*100:.0f}% reduction)")
