# main.py
from debate.context_mode import ContextMode
from debate.debate_controller import DebateController
from agents.base_agent import DebateAgent

def sample_agents():
    return [
        DebateAgent(
            name="Dr. Sarah Chen",
            persona="calm, evidence-based",
            role="medical researcher",
            expertise="AI in healthcare & ethics",
            style="professional"    
        ),
        DebateAgent(
            name="Marcus Rivera",
            persona="optimistic, tech-forward",
            role="startup founder",
            expertise="AI entrepreneurship",
            style="casual"
        ),
        DebateAgent(
            name="Prof. Elena Vasquez",
            persona="thoughtful, ethical",
            role="philosopher",
            expertise="AI ethics",
            style="academic"
        )
    ]

def ask_context_mode() -> ContextMode:
    print(
        "\nContext options:\n"
        "  1 → FULL        (entire chat each turn)\n"
        "  2 → SUMMARIZED  (rolling summary only)\n"
        "  3 → HYBRID      (summary + last few messages)  [default]"
    )
    choice = input("Select 1, 2 or 3  ▶ ").strip()
    return {
        "1": ContextMode.FULL,
        "2": ContextMode.SUMMARIZED,
        "3": ContextMode.HYBRID,
        "": ContextMode.HYBRID
    }.get(choice, ContextMode.HYBRID)

def ask_batching_preference():
    """Ask user about batching preference"""
    print("\n⚡ BATCHING OPTIMIZATION:")
    print("  Batching combines multiple agent responses into 1 API call")
    print("  • PRO: ~66% fewer API calls, faster execution, lower costs")
    print("  • CON: Less reliable parsing, shared context between agents")
    print()
    
    choice = input("Enable batching? (y/N): ").strip().lower()
    use_batching = choice.startswith('y')
    
    if use_batching:
        print("✅ Batching ENABLED - Agents will respond simultaneously")
    else:
        print("❌ Batching DISABLED - Agents will respond individually")
    
    return use_batching

def ask_length_limits():
    """Ask user about length limits and configure if enabled"""
    print("\n📏 LENGTH LIMITS:")
    print("  Enforce word limits on agent responses")
    print("  • PRO: ~60-70% fewer tokens, faster responses, lower costs")
    print("  • CON: Shorter arguments, may cut off detailed explanations")
    print()
    
    choice = input("Enable length limits? (y/N): ").strip().lower()
    use_length_limits = choice.startswith('y')
    
    if not use_length_limits:
        print("❌ Length limits DISABLED - Natural response lengths")
        return False, None
    
    print("✅ Length limits ENABLED")
    print("\n📏 Configure word limits for each debate stage:")
    print("(Press Enter for defaults)")
    
    # Get word limits from user
    opening_input = input("Opening statements word limit [100]: ").strip()
    opening_words = int(opening_input) if opening_input.isdigit() else 100
    
    rebuttal_input = input("Rebuttal word limit [75]: ").strip()
    rebuttal_words = int(rebuttal_input) if rebuttal_input.isdigit() else 75
    
    closing_input = input("Closing arguments word limit [125]: ").strip()
    closing_words = int(closing_input) if closing_input.isdigit() else 125
    
    word_limits = {
        "opening": {"words": opening_words, "tokens": opening_words * 2},
        "rebuttal": {"words": rebuttal_words, "tokens": rebuttal_words * 2},
        "closing": {"words": closing_words, "tokens": closing_words * 2}
    }
    
    print(f"✅ Word limits set: Opening({opening_words}), Rebuttal({rebuttal_words}), Closing({closing_words})")
    return True, word_limits

def ask_rag_preference():
    """Ask user about RAG knowledge retrieval"""
    print("\n📚 RAG KNOWLEDGE RETRIEVAL:")
    print("  Agents access domain-specific documents during debates")
    print("  • PRO: More accurate, source-backed arguments")
    print("  • CON: Requires document setup, slightly slower")
    print()
    
    choice = input("Enable RAG knowledge retrieval? (y/N): ").strip().lower()
    use_rag = choice.startswith('y')
    
    if use_rag:
        print("✅ RAG ENABLED - Agents will access domain knowledge")
        # Check if RAG system is available
        try:
            from rag.retriever import KnowledgeRetriever
            retriever = KnowledgeRetriever()
            domains = retriever.available_domains()
            if domains:
                print(f"   Available knowledge domains: {', '.join(domains)}")
            else:
                print("   ⚠️  No knowledge bases found. Run 'python rag/indexer.py' first")
        except ImportError:
            print("   ⚠️  RAG system not available")
    else:
        print("❌ RAG DISABLED - Agents use only training knowledge")
    
    return use_rag

def run():
    print("\n🗣️  DebAIte – Multi-Agent Debate Simulator")
    print("==========================================")

    # 1) Topic
    topic = input("Debate topic ▶ ").strip()
    if not topic:
        topic = "Should governments impose strict regulations on AI research?"
        print(f"(Default topic selected → {topic})")

    # 2) Agents
    agents = sample_agents()
    print(f"\nLoaded {len(agents)} agents:")
    for ag in agents:
        print(" •", ag)

    # 3) Context mode
    mode = ask_context_mode()
    
    # 4) ASK FOR OPTIMIZATIONS HERE!
    use_batching = ask_batching_preference()
    use_length_limits, word_limits = ask_length_limits()
    use_rag = ask_rag_preference()
    
    # 5) Summary of selections
    print(f"\n📋 CONFIGURATION SUMMARY:")
    print(f"   Context Mode: {mode.value.upper()}")
    print(f"   Batching: {'✅ ENABLED' if use_batching else '❌ DISABLED'}")
    print(f"   Length Limits: {'✅ ENABLED' if use_length_limits else '❌ DISABLED'}")
    print(f"   RAG Knowledge: {'✅ ENABLED' if use_rag else '❌ DISABLED'}")
    
    if word_limits:
        print(f"   Word Limits: Opening({word_limits['opening']['words']}), "
              f"Rebuttal({word_limits['rebuttal']['words']}), "
              f"Closing({word_limits['closing']['words']})")

    input("\nPress <Enter> to begin the debate…")

    # 6) Fire up the controller with all user selections
    DebateController(
        agents=agents,
        topic=topic,
        context_mode=mode,
        use_batching=use_batching,
        use_length_limits=use_length_limits,
        word_limits=word_limits,
        use_rag=use_rag
    ).run()

if __name__ == "__main__":
    run()
    