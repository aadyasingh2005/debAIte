from debate.context_mode import ContextMode
from debate.debate_controller import DebateController
from agents.base_agent import DebateAgent
from agents.template_loader import TemplateLoader

def ask_context_mode() -> ContextMode:
    """Interactive prompt for context mode"""
    print("\nContext options:")
    print("  1 → FULL        (entire chat each turn)")
    print("  2 → SUMMARIZED  (rolling summary only)")
    print("  3 → HYBRID      (summary + last few messages)  [default]")
    choice = input("Select 1, 2 or 3  ▶ ").strip()
    return {
        "1": ContextMode.FULL,
        "2": ContextMode.SUMMARIZED,
        "3": ContextMode.HYBRID,
        "": ContextMode.HYBRID
    }.get(choice, ContextMode.HYBRID)

def select_agents_from_templates() -> list:
    """Let user pick agents from personality templates"""
    loader = TemplateLoader()
    
    print("\n📋 Available Agent Templates:")
    print("=" * 50)
    
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
    
    agents = loader.create_multiple_agents(selected_templates)
    
    print(f"\n✅ Selected {len(agents)} agents:")
    for agent in agents:
        print(f"   • {agent}")
    
    return agents

def create_custom_agent() -> DebateAgent:
    """Create a custom agent interactively"""
    print("\n🛠️ Create Custom Agent:")
    name = input("Name: ").strip() or "Custom Agent"
    persona = input("Personality (e.g., 'calm, logical'): ").strip() or "balanced, thoughtful"
    role = input("Role (e.g., 'teacher', 'scientist'): ").strip() or "expert"
    expertise = input("Area of expertise: ").strip() or "general knowledge"
    style = input("Speaking style: ").strip() or "professional"
    
    return DebateAgent(name, persona, role, expertise, style)

def choose_agent_creation_method():
    """Let user choose how to create agents"""
    print("\nHow would you like to create agents?")
    print("  1 → Select from templates (recommended)")
    print("  2 → Create custom agents")
    print("  3 → Mix both")
    
    choice = input("Your choice (1-3) ▶ ").strip()
    
    if choice == "2":
        # Custom agents only
        agents = []
        num_agents = int(input("How many custom agents? (2-6): ") or "2")
        for i in range(num_agents):
            print(f"\n--- Agent {i+1} ---")
            agents.append(create_custom_agent())
        return agents
    
    elif choice == "3":
        # Mix templates and custom
        template_agents = select_agents_from_templates()
        
        add_custom = input("\nAdd custom agents? (y/n): ").lower().startswith('y')
        if add_custom:
            num_custom = int(input("How many custom agents to add? ") or "1")
            for i in range(num_custom):
                print(f"\n--- Custom Agent {i+1} ---")
                template_agents.append(create_custom_agent())
        
        return template_agents
    
    else:
        # Templates only (default)
        return select_agents_from_templates()

def run():
    print("\n🗣️  DebAIte – Multi-Agent Debate Simulator")
    print("==========================================")

    # 1. Topic
    topic = input("Debate topic ▶ ").strip()
    if not topic:
        topic = "Should governments impose strict regulations on AI research?"
        print(f"(Default topic selected → {topic})")

    # 2. Agent selection
    agents = choose_agent_creation_method()
    
    if len(agents) < 2:
        print("Need at least 2 agents for a debate!")
        return

    # 3. Context mode
    mode = ask_context_mode()
    print(f"\nRunning in {mode.value.upper()} mode…")

    input("\nPress <Enter> to begin the debate…")

    # 4. Run debate
    DebateController(
        agents=agents,
        topic=topic,
        context_mode=mode
    ).run()

if __name__ == "__main__":
    run()
