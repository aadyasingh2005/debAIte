from agents.base_agent import DebateAgent

agent1 = DebateAgent("Dr. Aria", "calm, logical", "public health expert")
agent2 = DebateAgent("Prof. Vale", "fiery, ethical", "philosopher")

topic = "Should AI be used to diagnose patients?"
for i in range(2):
    for agent in [agent1, agent2]:
        print(f"{agent.name}: {agent.respond(topic)}")     