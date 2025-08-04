# main.py
# ──────────────────────────────────────────────────────────────
# 1.   Run  →  python main.py
# 2.   Enter debate topic
# 3.   (Optionally edit topic by re-typing)
# 4.   Choose context-mode when prompted
# 5.   Debate starts

from debate.context_mode import ContextMode
from debate.debate_controller import DebateController
from agents.base_agent import DebateAgent


# ------------------------------------------------------------------
# Sample agents (swap out with your AgentBuilder if you like)
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# Utility: ask for mode *only* when we are about to start the debate
# ------------------------------------------------------------------
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
        "":  ContextMode.HYBRID   # Enter = default
    }.get(choice, ContextMode.HYBRID)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
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

    # 3) Ask for mode *right here*, just before starting
    mode = ask_context_mode()
    print(f"\nRunning in {mode.value.upper()} mode…")

    input("\nPress <Enter> to begin the debate…")

    # 4) Fire up the controller
    DebateController(
        agents=agents,
        topic=topic,
        context_mode=mode
    ).run()


if __name__ == "__main__":
    run()
