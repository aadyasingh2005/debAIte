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
        
        # Conditionally initialize RAG retriever
        if use_rag:
            try:
                from rag.retriever import KnowledgeRetriever
                self.knowledge_retriever = KnowledgeRetriever()
                print("✅ RAG knowledge retrieval enabled")
            except ImportError:
                print("⚠️  RAG system not available, continuing without knowledge retrieval")
                self.use_rag = False
        
        # Initialize conversation
        self.cm.start_debate(topic, agents)

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
            self._individual_round("rebuttal", None)  # Individual context per agent

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
            
            # Add RAG knowledge if enabled
            if self.use_rag:
                context = self._enhance_context_with_rag(agent, context, stage)
            
            # Generate response with or without length limits
            if self.use_length_limits:
                response = agent.respond(self.topic, context, 1, stage, self.word_limits)
            else:
                response = agent.respond(self.topic, context, 1, stage)
            
            self.cm.add_message(agent.name, response)
            print(f"\n{agent.name}: {response}")
            time.sleep(0.5)

    def _enhance_context_with_rag(self, agent, context: str, stage: str) -> str:
        """Add RAG knowledge to context if available"""
        # Map agent roles to knowledge domains
        domain_mapping = {
            "medical researcher": "medical",
            "startup founder": "tech", 
            "philosopher": "ethics",
            "lawyer": "legal",
            "economist": "economics"
        }
        
        domain = domain_mapping.get(agent.role.lower())
        if not domain:
            return context  # No domain mapping found
        
        # Create query from topic and current context
        query = f"{self.topic} {stage}"
        
        # Retrieve relevant knowledge
        rag_context = self.knowledge_retriever.get_context_string(domain, query, top_k=2)
        
        if rag_context:
            # Combine original context with RAG knowledge
            enhanced_context = f"{context}\n\n{rag_context}" if context else rag_context
            return enhanced_context
        
        return context

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
        
        if self.use_batching:
            estimated_calls = self.max_rounds
            saved_calls = (len(self.agents) * self.max_rounds) - estimated_calls
            print(f"  • API Calls Saved: {saved_calls} ({saved_calls//(len(self.agents) * self.max_rounds)*100:.0f}% reduction)")
