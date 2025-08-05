import json
import os
from typing import Dict, List
from agents.base_agent import DebateAgent

class TemplateLoader:
    def __init__(self, template_file="agents/personality_templates.json"):
        self.template_file = template_file
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load personality templates from JSON file"""
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Template file {self.template_file} not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing template file: {e}")
            return {}
    
    def get_template(self, template_id: str) -> Dict:
        """Get a specific personality template"""
        if template_id not in self._templates:
            raise ValueError(f"Template '{template_id}' not found. Available: {self.list_templates()}")
        return self._templates[template_id].copy()
    
    def list_templates(self) -> List[str]:
        """Get list of available template IDs"""
        return list(self._templates.keys())
    
    def get_template_info(self) -> Dict[str, str]:
        """Get template ID -> description mapping for UI"""
        return {
            template_id: data.get("description", f"{data.get('name', 'Unknown')} - {data.get('role', 'Unknown role')}")
            for template_id, data in self._templates.items()
        }
    
    def create_agent_from_template(self, template_id: str, custom_name: str = None) -> DebateAgent:
        """Create a DebateAgent from a template"""
        template = self.get_template(template_id)
        
        return DebateAgent(
            name=custom_name or template["name"],
            persona=template["persona"],
            role=template["role"],
            expertise=template["expertise"],
            style=template["style"]
        )
    
    def create_multiple_agents(self, template_ids: List[str]) -> List[DebateAgent]:
        """Create multiple agents from template IDs"""
        agents = []
        for template_id in template_ids:
            try:
                agent = self.create_agent_from_template(template_id)
                agents.append(agent)
            except ValueError as e:
                print(f"Warning: {e}")
        return agents
    
    def get_random_agents(self, count: int = 3) -> List[DebateAgent]:
        """Get random agents for quick demos"""
        import random
        template_ids = random.sample(self.list_templates(), min(count, len(self._templates)))
        return self.create_multiple_agents(template_ids)
