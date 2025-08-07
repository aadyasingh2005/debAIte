# test_all_agents.py
from agents.template_loader import TemplateLoader
from agents.model_providers import get_available_providers

def test_all_custom_agents():
    providers = get_available_providers()
    
    # Force selection of Ollama/phi3 (like in your debug script)
    model_provider = None
    for key, provider in providers.items():
        if 'ollama' in key.lower() or 'phi3' in provider.get_name().lower():
            model_provider = provider
            print(f"✅ Using: {provider.get_name()}")
            break
    
    if not model_provider:
        print("❌ Ollama/phi3 not found!")
        return
    
    loader = TemplateLoader()
    templates = loader.list_templates()
    
    print(f"\n🧪 Testing {len(templates)} agents:")
    print("=" * 80)
    
    results = {"success": [], "failed": []}
    
    for i, template_id in enumerate(templates, 1):
        print(f"\n[{i:2d}/{len(templates)}] Testing {template_id}...")
        
        try:
            # Create agent
            agent = loader.create_agent_from_template(template_id, model_provider=model_provider)
            
            # Check basic properties
            domain_status = "✅" if agent.knowledge_domain else "❌ None"
            print(f"   Name: {agent.name}")
            print(f"   Role: {agent.role}")
            print(f"   Domain: {agent.knowledge_domain} {domain_status}")
            
            # Test response generation
            response = agent.respond(
                topic="Should AI be regulated?",
                context="",
                round_number=1,
                stage="opening",
                use_rag=False  # Test without RAG first
            )
            
            if response.startswith("[Error"):
                print(f"   ❌ Response failed: {response}")
                results["failed"].append({"agent": agent.name, "template": template_id, "error": "Response generation failed"})
            else:
                print(f"   ✅ Response success: {len(response)} chars")
                # Show domain analysis if available
                if hasattr(agent, 'get_domain_analysis'):
                    analysis = agent.get_domain_analysis()
                    if analysis:
                        domain_sim = analysis.get('agent_domain_similarity', 0)
                        drift = analysis.get('drift_detected', False)
                        print(f"   📊 Domain similarity: {domain_sim:.3f}, Drift: {drift}")
                
                results["success"].append({"agent": agent.name, "template": template_id})
                
        except Exception as e:
            print(f"   ❌ Creation failed: {e}")
            results["failed"].append({"agent": "N/A", "template": template_id, "error": str(e)})
        
        print("-" * 50)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"✅ Successful: {len(results['success'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    
    if results["success"]:
        print(f"\n✅ Working agents:")
        for result in results["success"]:
            print(f"   • {result['agent']} ({result['template']})")
    
    if results["failed"]:
        print(f"\n❌ Failed agents:")
        for result in results["failed"]:
            print(f"   • {result['agent']} ({result['template']}): {result['error']}")
    
    # Quick fix suggestions
    failed_domains = [r for r in results["failed"] if "Domain: None" in str(r)]
    if failed_domains:
        print(f"\n💡 Quick Fix: Add 'knowledge_domain' field to these templates:")
        for result in results["failed"]:
            if "None" in str(result):
                print(f"   • {result['template']}")

if __name__ == "__main__":
    test_all_custom_agents()
