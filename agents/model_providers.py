import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class ModelProvider(ABC):
    """Abstract base class for different LLM providers"""
    
    @abstractmethod
    def generate_content(self, prompt: str, config: Dict[str, Any]) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass

class GeminiProvider(ModelProvider):
    """Google Gemini provider"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None
    
    def generate_content(self, prompt: str, config: Dict[str, Any]) -> str:
        if not self.model:
            raise Exception("Gemini API key not configured")
        
        # Convert config to Gemini format
        gen_config = genai.GenerationConfig(
            temperature=config.get('temperature', 0.7),
            max_output_tokens=config.get('max_tokens', 500),
            top_p=config.get('top_p', 0.95),
            top_k=config.get('top_k', 40)
        )
        
        response = self.model.generate_content(prompt, generation_config=gen_config)
        return response.text.strip()
    
    def is_available(self) -> bool:
        return self.model is not None and os.getenv("GEMINI_API_KEY") is not None
    
    def get_name(self) -> str:
        return "Google Gemini (gemini-1.5-flash)"

class OllamaProvider(ModelProvider):
    """Ollama provider for local models"""
    
    def __init__(self, model_name="phi3"):
        self.model_name = model_name
        self._ollama_client = None
    
    def _get_ollama_client(self):
        if self._ollama_client is None:
            try:
                import ollama
                self._ollama_client = ollama
                self._ollama_client.list()
            except ImportError:
                raise Exception("Ollama library not installed. Run: pip install ollama")
            except Exception as e:
                raise Exception(f"Ollama service not running: {e}")
        return self._ollama_client

    def is_available(self) -> bool:
        try:
            client = self._get_ollama_client()
            models_response = client.list()
            
            # Extract model names
            model_names = []
            if hasattr(models_response, 'get') and 'models' in models_response:
                models = models_response['models']
            elif hasattr(models_response, 'models'):
                models = models_response.models
            else:
                models = models_response
            
            for model in models:
                if isinstance(model, dict):
                    name = model.get('name', '')
                elif hasattr(model, 'name'):
                    name = model.name
                else:
                    name = str(model)
                
                model_names.append(name.lower())
            
            # Look for phi3 in any variant
            return any(self.model_name.lower() in name for name in model_names)
            
        except Exception:
            return False
    
    def generate_content(self, prompt: str, config: Dict[str, Any]) -> str:
        client = self._get_ollama_client()
        
        # Use chat format for better results
        response = client.chat(
            model=self.model_name,
            messages=[
                {'role': 'user', 'content': prompt}
            ],
            options={
                'temperature': config.get('temperature', 0.7),
                'num_predict': config.get('max_tokens', 500),
                'top_p': config.get('top_p', 0.95),
                'top_k': config.get('top_k', 40)
            }
        )
        
        return response['message']['content'].strip()
    
    def get_name(self) -> str:
        return f"Ollama ({self.model_name})"

def get_available_providers() -> Dict[str, ModelProvider]:
    """Get all available model providers"""
    providers = {}
    
    # Check Gemini
    gemini = GeminiProvider()
    if gemini.is_available():
        providers['gemini'] = gemini
    
    # Check Ollama Phi3
    ollama_phi3 = OllamaProvider("phi3")
    if ollama_phi3.is_available():
        providers['ollama_phi3'] = ollama_phi3
    
    return providers
