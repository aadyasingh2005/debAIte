from ..agents.template_loader import TemplateLoader
from ..agents.model_providers import get_available_providers

def test_hybrid_domain_control():
    providers = get_available_providers()
    model_provider = list(providers.values())[0]
    
    loader = TemplateLoader()
    
    # Create agents
    medical_agent = loader.create_agent_from_template("medical_expert", model_provider=model_provider)
    tech_agent = loader.create_agent_from_template("tech_entrepreneur", model_provider=model_provider)
    
    # Test topic that could cause domain drift
    topic = "What are the drawbacks of invasive medical procedures"
    
    print("🏥 MEDICAL AGENT Response:")
    print("=" * 60)
    medical_response = medical_agent.respond(topic, "", 1, "opening", use_rag=True)
    print(medical_response)
    
    medical_analysis = medical_agent.get_domain_analysis()
    print(f"\n📊 Domain Analysis:")
    print(f"Medical similarity: {medical_analysis['agent_domain_similarity']:.3f}")
    print(f"Drift detected: {medical_analysis['drift_detected']}")
    print(f"All similarities: {medical_analysis['all_similarities']}")
    
    print("\n" + "="*80)
    
    print("💻 TECH AGENT Response:")
    print("=" * 60)
    tech_response = tech_agent.respond(topic, "", 1, "opening", use_rag=True)
    print(tech_response)
    
    tech_analysis = tech_agent.get_domain_analysis()
    print(f"\n📊 Domain Analysis:")
    print(f"Tech similarity: {tech_analysis['agent_domain_similarity']:.3f}")
    print(f"Drift detected: {tech_analysis['drift_detected']}")
    print(f"All similarities: {tech_analysis['all_similarities']}")

if __name__ == "__main__":
    test_hybrid_domain_control()
