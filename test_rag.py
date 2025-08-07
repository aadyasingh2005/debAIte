from agents.template_loader import TemplateLoader
from agents.model_providers import get_available_providers

# Get your model provider
providers = get_available_providers()
model_provider = list(providers.values())[0]

# Create the same agent twice
loader = TemplateLoader()
agent1 = loader.create_agent_from_template("medical_expert", model_provider=model_provider)
agent2 = loader.create_agent_from_template("medical_expert", model_provider=model_provider)

topic = "Should AI replace doctors?"

# Test WITHOUT RAG
print("🚫 WITHOUT RAG:")
response_no_rag = agent1.respond(topic, "", 1, "opening", use_rag=False)
print(response_no_rag)

print("\n" + "="*50)

# Test WITH RAG  
print("📚 WITH RAG:")
response_with_rag = agent2.respond(topic, "", 1, "opening", use_rag=True)
print(response_with_rag)

print("\n" + "="*50)
print("RAG KNOWLEDGE RETRIEVED:")
print(agent2.retrieve_knowledge("AI replace doctors medical", True))
