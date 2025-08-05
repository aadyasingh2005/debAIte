# main.py
from debate.context_mode import ContextMode
from debate.debate_controller import DebateController
from agents.base_agent import DebateAgent
from agents.model_providers import get_available_providers
from agents.template_loader import TemplateLoader

def ask_model_provider():
    """Ask user which model provider to use"""
    print("\n🤖 MODEL PROVIDER SELECTION:")
    
    providers = get_available_providers()
    
    if not providers:
        print("❌ No model providers available!")
        print("   • For Gemini: Set GEMINI_API_KEY environment variable")
        print("   • For Ollama: Install Ollama and pull phi3 model")
        return None
    
    print("Available model providers:")
    provider_list = list(providers.items())
    
    for i, (key, provider) in enumerate(provider_list, 1):
        print(f"  {i} → {provider.get_name()}")
        if key == 'gemini':
            print("      • Cloud-based, fast, requires API key")
        elif key.startswith('ollama'):
            print("      • Local, private, no API key needed")
    
    while True:
        try:
            choice = input(f"Select provider (1-{len(provider_list)}) ▶ ").strip()
            if not choice:
                choice = "1"
            
            index = int(choice) - 1
            if 0 <= index < len(provider_list):
                selected_key, selected_provider = provider_list[index]
                print(f"✅ Selected: {selected_provider.get_name()}")
                return selected_provider
            else:
                print(f"Please enter a number between 1 and {len(provider_list)}")
        except ValueError:
            print("Please enter a valid number")

def choose_agent_creation_method(model_provider):
    """Let user choose how to create agents"""
    print("\n👥 AGENT CREATION:")
    print("How would you like to create agents?")
    print("  1 → Select from personality templates (recommended)")
    print("  2 → Use default 3-agent setup")
    print("  3 → Create custom agents")
    
    choice = input("Your choice (1-3) [1] ▶ ").strip() or "1"
    
    if choice == "2":
        # Default 3 agents
        return [
            DebateAgent(
                name="Dr. Sarah Chen",
                persona="calm, evidence-based",
                role="medical researcher",
                expertise="AI in healthcare & ethics",
                style="professional",
                knowledge_domain="medical",
                model_provider=model_provider
            ),
            DebateAgent(
                name="Marcus Rivera",
                persona="optimistic, tech-forward",
                role="startup founder",
                expertise="AI entrepreneurship",
                style="casual",
                knowledge_domain="tech",
                model_provider=model_provider
            ),
            DebateAgent(
                name="Prof. Elena Vasquez",
                persona="thoughtful, ethical",
                role="philosopher",
                expertise="AI ethics",
                style="academic",
                knowledge_domain="ethics",
                model_provider=model_provider
            )
        ]
    
    elif choice == "3":
        # Custom agents
        return create_custom_agents(model_provider)
    
    else:
        # Templates (default)
        return select_agents_from_templates(model_provider)

def select_agents_from_templates(model_provider):
    """Let user pick agents from personality templates"""
    loader = TemplateLoader()
    
    print("\n📋 Available Agent Templates:")
    print("=" * 60)
    
    templates = loader.get_template_info()
    template_list = list(templates.keys())
    
    for i, (template_id, description) in enumerate(templates.items(), 1):
        print(f"{i:2d}. {template_id.replace('_', ' ').title()}")
        print(f"    {description}")
        print()
    
    print("Select agents by entering numbers (e.g., '1,3,5' or '1-3'):")
    selection = input("Your choice ▶ ").strip()
    
    # Parse selection
    selected_indices = []
    if not selection:
        # Default selection
        selected_indices = [1, 2, 3]
        print("Using default selection: 1,2,3")
    else:
        for part in selection.split(','):
            part = part.strip()
            if '-' in part:
                # Range selection (e.g., "1-3")
                start, end = map(int, part.split('-'))
                selected_indices.extend(range(start, end + 1))
            else:
                selected_indices.append(int(part))
    
    # Convert to template IDs and create agents
    selected_templates = []
    for idx in selected_indices:
        if 1 <= idx <= len(template_list):
            selected_templates.append(template_list[idx - 1])
    
    # ✅ FIXED: Pass model_provider as keyword argument
    agents = loader.create_multiple_agents(selected_templates, model_provider=model_provider)
    
    print(f"\n✅ Selected {len(agents)} agents:")
    for agent in agents:
        print(f"   • {agent}")
    
    return agents

def create_custom_agents(model_provider):
    """Create custom agents interactively"""
    agents = []
    num_agents = int(input("How many custom agents? (2-6): ") or "3")
    
    for i in range(num_agents):
        print(f"\n🛠️  Create Agent {i+1}:")
        name = input("Name: ").strip() or f"Agent {i+1}"
        persona = input("Personality (e.g., 'calm, logical'): ").strip() or "balanced, thoughtful"
        role = input("Role (e.g., 'teacher', 'scientist'): ").strip() or "expert"
        expertise = input("Area of expertise: ").strip() or "general knowledge"
        style = input("Speaking style: ").strip() or "professional"
        
        agent = DebateAgent(
            name=name,
            persona=persona,
            role=role,
            expertise=expertise,
            style=style,
            model_provider=model_provider
        )
        agents.append(agent)
    
    return agents

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
    print("  • NOTE: Only works with Gemini (Ollama doesn't support batching)")
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

    # 1) Model Provider Selection
    model_provider = ask_model_provider()
    if not model_provider:
        print("Cannot proceed without a model provider. Exiting.")
        return

    # 2) Topic
    topic = input("\nDebate topic ▶ ").strip()
    if not topic:
        topic = "Should governments impose strict regulations on AI research?"
        print(f"(Default topic selected → {topic})")

    # 3) Agent Creation
    agents = choose_agent_creation_method(model_provider)
    
    if len(agents) < 2:
        print("Need at least 2 agents for a debate!")
        return

    # 4) Context mode
    mode = ask_context_mode()
    
    # 5) Optimizations
    use_batching = ask_batching_preference()
    
    # Disable batching for Ollama
    if use_batching and 'ollama' in model_provider.get_name().lower():
        print("⚠️  Batching not supported with Ollama, disabling batching")
        use_batching = False
    
    use_length_limits, word_limits = ask_length_limits()
    use_rag = ask_rag_preference()
    
    # 6) Configuration summary
    print(f"\n📋 CONFIGURATION SUMMARY:")
    print(f"   Model Provider: {model_provider.get_name()}")
    print(f"   Agents: {len(agents)} selected")
    print(f"   Context Mode: {mode.value.upper()}")
    print(f"   Batching: {'✅ ENABLED' if use_batching else '❌ DISABLED'}")
    print(f"   Length Limits: {'✅ ENABLED' if use_length_limits else '❌ DISABLED'}")
    print(f"   RAG Knowledge: {'✅ ENABLED' if use_rag else '❌ DISABLED'}")
    
    if word_limits:
        print(f"   Word Limits: Opening({word_limits['opening']['words']}), "
              f"Rebuttal({word_limits['rebuttal']['words']}), "
              f"Closing({word_limits['closing']['words']})")

    input("\nPress <Enter> to begin the debate…")

    # 7) Run debate
    DebateController(
        agents=agents,
        topic=topic,
        context_mode=mode,
        use_batching=use_batching,
        use_length_limits=use_length_limits,
        word_limits=word_limits,
        use_rag=use_rag
    ).run()
def choose_agent_creation_method(model_provider):
    """Let user choose how to create agents"""
    print("\n👥 AGENT CREATION:")
    print("How would you like to create agents?")
    print("  1 → Select from personality templates (recommended)")
    print("  2 → Use default 3-agent setup")
    print("  3 → Create custom agents")
    
    choice = input("Your choice (1-3) [1] ▶ ").strip() or "1"
    
    if choice == "2":
        # Default 3 agents - create and then set model provider
        agents = [
            DebateAgent(
                name="Dr. Sarah Chen",
                persona="calm, evidence-based",
                role="medical researcher",
                expertise="AI in healthcare & ethics",
                style="professional",
                knowledge_domain="medical"
            ),
            DebateAgent(
                name="Marcus Rivera",
                persona="optimistic, tech-forward",
                role="startup founder",
                expertise="AI entrepreneurship",
                style="casual",
                knowledge_domain="tech"
            ),
            DebateAgent(
                name="Prof. Elena Vasquez",
                persona="thoughtful, ethical",
                role="philosopher",
                expertise="AI ethics",
                style="academic",
                knowledge_domain="ethics"
            )
        ]
        
        # Set model provider for all agents
        for agent in agents:
            agent.model_provider = model_provider
        
        return agents
    
    elif choice == "3":
        # Custom agents
        return create_custom_agents(model_provider)
    
    else:
        # Templates (default)
        return select_agents_from_templates(model_provider)

def create_custom_agents(model_provider):
    """Create custom agents interactively"""
    agents = []
    num_agents = int(input("How many custom agents? (2-6): ") or "3")
    
    for i in range(num_agents):
        print(f"\n🛠️  Create Agent {i+1}:")
        name = input("Name: ").strip() or f"Agent {i+1}"
        persona = input("Personality (e.g., 'calm, logical'): ").strip() or "balanced, thoughtful"
        role = input("Role (e.g., 'teacher', 'scientist'): ").strip() or "expert"
        expertise = input("Area of expertise: ").strip() or "general knowledge"
        style = input("Speaking style: ").strip() or "professional"
        
        agent = DebateAgent(
            name=name,
            persona=persona,
            role=role,
            expertise=expertise,
            style=style
        )
        
        # Set model provider after creation
        agent.model_provider = model_provider
        agents.append(agent)
    
    return agents

if __name__ == "__main__":
    run()
