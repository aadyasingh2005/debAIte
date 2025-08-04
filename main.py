from agents.base_agent import DebateAgent
from debate.debate_controller import DebateController

def create_sample_agents():
    """Create some sample agents for testing"""
    agents = [
        DebateAgent(
            name="Dr. Sarah Chen",
            persona="analytical, evidence-based, cautious",
            role="medical researcher",
            expertise_area="AI in healthcare and medical ethics",
            speaking_style="professional, uses medical terminology"
        ),
        DebateAgent(
            name="Marcus Rivera",
            persona="optimistic, tech-forward, entrepreneurial", 
            role="tech startup founder",
            expertise_area="AI innovation and business applications",
            speaking_style="casual, energetic, uses business terminology"
        ),
        DebateAgent(
            name="Prof. Elena Vasquez",
            persona="thoughtful, concerned, philosophical",
            role="ethics professor",
            expertise_area="AI ethics and social implications",
            speaking_style="academic, measured, asks probing questions"
        )
    ]
    return agents

def run_interactive_debate():
    """Run an interactive debate session"""
    print("🗣️ Welcome to DebAIte - Multi-Agent Debate Simulator")
    print("=" * 50)
    
    # Get debate topic from user
    topic = input("Enter debate topic: ").strip()
    if not topic:
        topic = "Should AI systems be required to explain their decisions?"
        print(f"Using default topic: {topic}")
    
    # Create agents (you can later make this user-configurable)
    agents = create_sample_agents()
    
    print(f"\nCreated {len(agents)} agents:")
    for agent in agents:
        print(f"- {agent}")
    
    print(f"\nStarting debate on: {topic}")
    input("Press Enter to begin...")
    
    # Run the debate
    controller = DebateController(agents, topic)
    conversation_history = controller.run_structured_debate()
    
    return conversation_history

if __name__ == "__main__":
    run_interactive_debate()
