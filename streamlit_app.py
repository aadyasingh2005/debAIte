import streamlit as st
import time
from datetime import datetime
from agents.template_loader import TemplateLoader
from agents.model_providers import get_available_providers
from debate.context_mode import ContextMode
from debate.debate_controller import DebateController

# Page config
st.set_page_config(
    page_title="DebAIte - AI Debate Simulator",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .debate-response {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    .config-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .enabled { background: #d4edda; color: #155724; }
    .disabled { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'debate_started' not in st.session_state:
        st.session_state.debate_started = False
    if 'agents' not in st.session_state:
        st.session_state.agents = []
    if 'debate_history' not in st.session_state:
        st.session_state.debate_history = []
    if 'current_round' not in st.session_state:
        st.session_state.current_round = 0
    if 'model_provider' not in st.session_state:
        st.session_state.model_provider = None

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🗣️ DebAIte</h1>
        <p>Multi-Agent AI Debate Simulator</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model Provider Selection
        model_provider = setup_model_provider()
        
        # Topic Input
        topic = st.text_input(
            "🎯 Debate Topic",
            value="Should governments impose strict regulations on AI research?",
            help="Enter the topic you want the agents to debate"
        )
        
        # Agent Selection
        agents = setup_agents(model_provider)
        
        # Debate Settings
        settings = setup_debate_settings()
        
        # Start Debate Button
        if st.button("🚀 Start Debate", type="primary", use_container_width=True):
            if len(agents) >= 2 and model_provider and topic:
                start_debate(topic, agents, model_provider, settings)
            else:
                st.error("Please configure at least 2 agents, select a model provider, and enter a topic.")
    
    # Main content area
    if st.session_state.debate_started:
        display_debate_interface()
    else:
        display_welcome_screen()

def setup_model_provider():
    """Model provider selection UI"""
    st.subheader("🤖 Model Provider")
    
    providers = get_available_providers()
    if not providers:
        st.error("❌ No model providers available!")
        st.info("• For Gemini: Set GEMINI_API_KEY\n• For Ollama: Install Ollama and pull phi3")
        return None
    
    provider_names = [f"{provider.get_name()}" for provider in providers.values()]
    selected_name = st.selectbox("Choose Provider", provider_names)
    
    if selected_name:
        # Find the provider object
        for provider in providers.values():
            if provider.get_name() == selected_name:
                st.session_state.model_provider = provider
                return provider
    
    return None

def setup_agents(model_provider):
    """Agent selection UI"""
    st.subheader("👥 Agents")
    
    if not model_provider:
        st.warning("Select a model provider first")
        return []
    
    # Agent creation method
    creation_method = st.radio(
        "Agent Creation",
        ["Templates", "Default Set", "Custom"],
        help="Choose how to create your debate agents"
    )
    
    if creation_method == "Templates":
        return setup_template_agents(model_provider)
    elif creation_method == "Default Set":
        return setup_default_agents(model_provider)
    else:
        return setup_custom_agents(model_provider)

def setup_template_agents(model_provider):
    """Template-based agent selection"""
    loader = TemplateLoader()
    templates = loader.get_template_info()
    
    # Multi-select for templates
    template_names = list(templates.keys())
    template_labels = [f"{name.replace('_', ' ').title()}" for name in template_names]
    
    selected_labels = st.multiselect(
        "Select Agent Templates",
        template_labels,
        default=template_labels[:3] if len(template_labels) >= 3 else template_labels,
        help="Choose 2-6 agents for the debate"
    )
    
    # Create agents from selected templates
    agents = []
    for label in selected_labels:
        # Convert label back to template name
        template_name = template_names[template_labels.index(label)]
        try:
            agent = loader.create_agent_from_template(template_name, model_provider=model_provider)
            agents.append(agent)
        except Exception as e:
            st.error(f"Error creating agent {label}: {e}")
    
    # Display selected agents
    if agents:
        st.write("**Selected Agents:**")
        for agent in agents:
            st.markdown(f"""
            <div class="agent-card">
                <strong>{agent.name}</strong> ({agent.role})<br>
                <small>{agent.persona} • {agent.knowledge_domain or 'General'}</small>
            </div>
            """, unsafe_allow_html=True)
    
    return agents

def setup_default_agents(model_provider):
    """Default 3-agent setup"""
    from agents.base_agent import DebateAgent
    
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
    
    st.write("**Default Agents:**")
    for agent in agents:
        st.markdown(f"""
        <div class="agent-card">
            <strong>{agent.name}</strong> ({agent.role})<br>
            <small>{agent.persona} • {agent.knowledge_domain}</small>
        </div>
        """, unsafe_allow_html=True)
    
    return agents

def setup_custom_agents(model_provider):
    """Custom agent creation"""
    st.write("Custom agent creation coming soon!")
    return []

def setup_debate_settings():
    """Debate configuration settings"""
    st.subheader("🎛️ Settings")
    
    # Context Mode
    context_mode = st.selectbox(
        "Context Mode",
        ["HYBRID", "FULL", "SUMMARIZED"],
        help="How much conversation history to include"
    )
    
    # Optimizations
    st.write("**Optimizations:**")
    
    use_batching = st.checkbox(
        "⚡ Batching",
        help="Combine multiple agent responses (Gemini only)"
    )
    
    use_length_limits = st.checkbox(
        "📏 Length Limits",
        help="Enforce word limits on responses"
    )
    
    word_limits = None
    if use_length_limits:
        col1, col2, col3 = st.columns(3)
        with col1:
            opening_words = st.number_input("Opening", min_value=50, max_value=200, value=100)
        with col2:
            rebuttal_words = st.number_input("Rebuttal", min_value=50, max_value=150, value=75)
        with col3:
            closing_words = st.number_input("Closing", min_value=75, max_value=250, value=125)
        
        word_limits = {
            "opening": {"words": opening_words, "tokens": opening_words * 2},
            "rebuttal": {"words": rebuttal_words, "tokens": rebuttal_words * 2},
            "closing": {"words": closing_words, "tokens": closing_words * 2}
        }
    
    use_rag = st.checkbox(
        "📚 RAG Knowledge",
        value=True,
        help="Enable knowledge retrieval from domain documents"
    )
    
    if use_rag:
        try:
            from rag.retriever import KnowledgeRetriever
            retriever = KnowledgeRetriever()
            domains = retriever.available_domains()
            if domains:
                st.success(f"Available domains: {', '.join(domains)}")
            else:
                st.warning("No knowledge bases found")
        except ImportError:
            st.warning("RAG system not available")
    
    return {
        'context_mode': getattr(ContextMode, context_mode),
        'use_batching': use_batching,
        'use_length_limits': use_length_limits,
        'word_limits': word_limits,
        'use_rag': use_rag
    }

def start_debate(topic, agents, model_provider, settings):
    """Initialize and start the debate"""
    st.session_state.debate_started = True
    st.session_state.agents = agents
    st.session_state.topic = topic
    st.session_state.settings = settings
    st.session_state.debate_history = []
    st.session_state.current_round = 0
    
    # Disable batching for Ollama
    if settings['use_batching'] and 'ollama' in model_provider.get_name().lower():
        settings['use_batching'] = False
        st.warning("Batching disabled for Ollama")
    
    st.success("🎯 Debate started!")
    st.rerun()

def display_welcome_screen():
    """Welcome screen when no debate is active"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ## Welcome to DebAIte! 🗣️
        
        **Features:**
        - 🤖 Multiple AI model support (Gemini, Ollama)
        - 👥 10+ personality templates or custom agents
        - 📚 RAG-enhanced domain expertise
        - ⚡ Performance optimizations
        - 🎯 Real-time debate simulation
        
        **Get Started:**
        1. Choose your model provider in the sidebar
        2. Select agents and configure settings
        3. Enter a debate topic
        4. Click "Start Debate" to begin!
        
        **Example Topics:**
        - Should AI replace human teachers?
        - Is universal basic income necessary due to AI automation?
        - Should there be a global ban on lethal autonomous weapons?
        """)

def display_debate_interface():
    """Main debate interface"""
    # Debate header
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"## 🎯 {st.session_state.topic}")
    
    with col2:
        if st.button("🔄 New Debate"):
            reset_debate()
            st.rerun()
    
    # Configuration summary
    settings = st.session_state.settings
    st.markdown(f"""
    <div class="config-section">
        <strong>Configuration:</strong> 
        {len(st.session_state.agents)} agents • 
        {settings['context_mode'].value} context • 
        <span class="status-badge {'enabled' if settings['use_rag'] else 'disabled'}">
            RAG {'✅' if settings['use_rag'] else '❌'}
        </span> •
        <span class="status-badge {'enabled' if settings['use_length_limits'] else 'disabled'}">
            Length Limits {'✅' if settings['use_length_limits'] else '❌'}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Debate controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Next Round", type="primary"):
            run_debate_round()
    
    with col2:
        if st.button("⏭️ Skip to End"):
            run_full_debate()
    
    with col3:
        if st.button("📊 Generate Summary"):
            generate_debate_summary()
    
    # Display debate history
    display_debate_history()

def run_debate_round():
    """Run a single round of the debate"""
    current_round = st.session_state.current_round
    agents = st.session_state.agents
    settings = st.session_state.settings
    
    # Determine stage
    if current_round == 0:
        stage = "opening"
        stage_title = "Opening Statements"
    elif current_round < 3:
        stage = "rebuttal"
        stage_title = f"Rebuttal Round {current_round}"
    else:
        stage = "closing"
        stage_title = "Closing Arguments"
    
    # Progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Round header
    st.markdown(f"### 🗣️ Round {current_round + 1}: {stage_title}")
    
    if settings['use_length_limits'] and settings['word_limits']:
        word_limit = settings['word_limits'][stage]['words']
        st.info(f"📏 Word limit: {word_limit} words")
    
    # Generate responses for each agent
    round_responses = []
    
    for i, agent in enumerate(agents):
        status_text.text(f"💭 {agent.name} is thinking...")
        progress_bar.progress((i + 1) / len(agents))
        
        # Get context (simplified for MVP)
        context = "\n".join([f"{h['agent']}: {h['response'][:200]}..." 
                           for h in st.session_state.debate_history[-3:]])
        
        try:
            # Generate response
            response = agent.respond(
                topic=st.session_state.topic,
                context=context,
                round_number=current_round + 1,
                stage=stage,
                word_limits=settings['word_limits'] if settings['use_length_limits'] else None,
                use_rag=settings['use_rag']
            )
            
            # Display response
            st.markdown(f"""
            <div class="debate-response">
                <h4>🎭 {agent.name} ({agent.role})</h4>
                <p>{response}</p>
                <small>
                    🏷️ {agent.knowledge_domain or 'General'} • 
                    ⏱️ {datetime.now().strftime('%H:%M')}
                    {' • 📚 RAG Enhanced' if settings['use_rag'] and agent.knowledge_domain else ''}
                </small>
            </div>
            """, unsafe_allow_html=True)
            
            # Store in history
            round_responses.append({
                'round': current_round + 1,
                'stage': stage,
                'agent': agent.name,
                'role': agent.role,
                'response': response,
                'timestamp': datetime.now(),
                'domain': agent.knowledge_domain
            })
            
            time.sleep(0.5)  # Brief pause for better UX
            
        except Exception as e:
            st.error(f"Error generating response for {agent.name}: {e}")
    
    # Update session state
    st.session_state.debate_history.extend(round_responses)
    st.session_state.current_round += 1
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Auto-advance for next round
    if current_round < 3:
        st.info("👆 Click 'Next Round' to continue the debate")
    else:
        st.success("🎉 Debate completed! Generate a summary to see the results.")

def run_full_debate():
    """Run the complete debate automatically"""
    st.info("🚀 Running full debate automatically...")
    
    for round_num in range(4):  # 4 total rounds
        if st.session_state.current_round <= round_num:
            run_debate_round()
            time.sleep(1)

def display_debate_history():
    """Display the debate history"""
    if not st.session_state.debate_history:
        st.info("👆 Start the debate to see responses here")
        return
    
    # Group by rounds
    rounds = {}
    for entry in st.session_state.debate_history:
        round_num = entry['round']
        if round_num not in rounds:
            rounds[round_num] = []
        rounds[round_num].append(entry)
    
    # Display each round
    for round_num in sorted(rounds.keys()):
        with st.expander(f"Round {round_num}: {rounds[round_num][0]['stage'].title()}", expanded=True):
            for entry in rounds[round_num]:
                st.markdown(f"""
                <div class="debate-response">
                    <h4>🎭 {entry['agent']} ({entry['role']})</h4>
                    <p>{entry['response']}</p>
                    <small>
                        🏷️ {entry['domain'] or 'General'} • 
                        ⏱️ {entry['timestamp'].strftime('%H:%M')}
                    </small>
                </div>
                """, unsafe_allow_html=True)

def generate_debate_summary():
    """Generate a summary of the debate"""
    if not st.session_state.debate_history:
        st.warning("No debate history to summarize")
        return
    
    st.markdown("## 📊 Debate Summary")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Rounds", st.session_state.current_round)
    
    with col2:
        st.metric("Total Responses", len(st.session_state.debate_history))
    
    with col3:
        agents_count = len(set(entry['agent'] for entry in st.session_state.debate_history))
        st.metric("Active Agents", agents_count)
    
    with col4:
        avg_length = sum(len(entry['response'].split()) for entry in st.session_state.debate_history) / len(st.session_state.debate_history)
        st.metric("Avg Response Length", f"{avg_length:.0f} words")
    
    # Agent participation
    st.subheader("👥 Agent Participation")
    agent_stats = {}
    for entry in st.session_state.debate_history:
        agent = entry['agent']
        if agent not in agent_stats:
            agent_stats[agent] = {'responses': 0, 'words': 0, 'domain': entry['domain']}
        agent_stats[agent]['responses'] += 1
        agent_stats[agent]['words'] += len(entry['response'].split())
    
    for agent, stats in agent_stats.items():
        st.markdown(f"""
        <div class="agent-card">
            <strong>{agent}</strong><br>
            📝 {stats['responses']} responses • 
            📊 {stats['words']} total words • 
            🏷️ {stats['domain'] or 'General'} domain
        </div>
        """, unsafe_allow_html=True)

def reset_debate():
    """Reset the debate state"""
    st.session_state.debate_started = False
    st.session_state.debate_history = []
    st.session_state.current_round = 0

if __name__ == "__main__":
    main()
