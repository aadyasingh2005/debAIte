import google.generativeai as genai
from typing import List, Dict

class BatchDebateProcessor:
    """Handles batched requests for multiple agents"""
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def create_batch_prompt(self, agents: List, topic: str, context: str, stage: str, word_limits=None) -> str:
        """Create a single prompt that generates responses for all agents"""
        
        # Get word limits
        if word_limits:
            word_limit = word_limits.get(stage, {"words": 100})["words"]
        else:
            word_limit = 150  # Default reasonable length
        
        # Build agent descriptions
        agent_descriptions = []
        for i, agent in enumerate(agents, 1):
            desc = f"Agent {i} - {agent.name}: {agent.persona} {agent.role}"
            if agent.expertise:
                desc += f", expertise in {agent.expertise}"
            if agent.style:
                desc += f", {agent.style} style"
            agent_descriptions.append(desc)
        
        # Stage instructions
        stage_instructions = {
            "opening": "Each agent should give their opening position on the topic.",
            "rebuttal": "Each agent should rebut the previous arguments while maintaining their perspective.",
            "closing": "Each agent should make their final closing argument."
        }
        
        # Build the mega-prompt
        batch_prompt = f"""You are facilitating a debate between multiple AI agents. Generate responses for each agent according to their personality and role.

TOPIC: {topic}

AGENTS:
{chr(10).join(agent_descriptions)}

STAGE: {stage.title()} - {stage_instructions.get(stage, 'Continue the debate')}

"""
        
        if context:
            batch_prompt += f"PREVIOUS ARGUMENTS:\n{context}\n\n"
        
        batch_prompt += f"""INSTRUCTIONS:
- Generate exactly one response for each agent
- Each response must be EXACTLY {word_limit} words or fewer
- Stay true to each agent's personality and expertise
- Responses should feel authentic to each character
- Be concise and impactful within the word limit
- Format your output exactly as shown below

OUTPUT FORMAT:
AGENT_1: [Agent 1's response here - max {word_limit} words]
AGENT_2: [Agent 2's response here - max {word_limit} words]
AGENT_3: [Agent 3's response here - max {word_limit} words]

Generate the responses now:"""
        
        return batch_prompt
    
    def parse_batch_response(self, response_text: str, agents: List) -> Dict[str, str]:
        """Parse the batched response back into individual agent responses"""
        responses = {}
        lines = response_text.strip().split('\n')
        
        current_agent = None
        current_response = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('AGENT_'):
                # Save previous agent's response
                if current_agent and current_response:
                    responses[current_agent] = ' '.join(current_response).strip()
                
                # Start new agent
                try:
                    agent_num = int(line.split('_')[1].split(':')[0]) - 1
                    if 0 <= agent_num < len(agents):
                        current_agent = agents[agent_num].name
                        # Get the text after the colon
                        response_part = line.split(':', 1)[1].strip() if ':' in line else ''
                        current_response = [response_part] if response_part else []
                except (ValueError, IndexError):
                    continue
            elif current_agent and line:
                current_response.append(line)
        
        # Don't forget the last agent
        if current_agent and current_response:
            responses[current_agent] = ' '.join(current_response).strip()
        
        # Fallback: if parsing failed, create basic responses
        if len(responses) != len(agents):
            print("⚠️  Batch parsing incomplete, filling missing responses...")
            for i, agent in enumerate(agents):
                if agent.name not in responses:
                    responses[agent.name] = f"[Batch response parsing incomplete for {agent.name}]"
        
        return responses
    
    def batch_respond(self, agents: List, topic: str, context: str, stage: str, word_limits=None) -> Dict[str, str]:
        """Generate responses for all agents in a single API call"""
        
        # Create batch prompt
        batch_prompt = self.create_batch_prompt(agents, topic, context, stage, word_limits)
        
        # Get appropriate config for the stage
        from agents.base_agent import get_creative_config
        config = get_creative_config(stage, word_limits)
        # Increase max tokens since we're generating multiple responses
        config.max_output_tokens = config.max_output_tokens * len(agents) + 100  # Extra buffer
        
        try:
            print(f"🔄 Generating {len(agents)} responses in batch...")
            
            # Single API call for all agents
            response = self.model.generate_content(batch_prompt, generation_config=config)
            
            # Parse the response
            responses = self.parse_batch_response(response.text, agents)
            
            print(f"✅ Batch processing successful!")
            return responses
            
        except Exception as e:
            # Fallback to individual calls if batching fails
            print(f"❌ Batch processing failed ({e})")
            print("🔄 Falling back to individual API calls...")
            return self._fallback_individual_calls(agents, topic, context, stage, word_limits)
    
    def _fallback_individual_calls(self, agents: List, topic: str, context: str, stage: str, word_limits=None) -> Dict[str, str]:
        """Fallback to individual API calls if batching fails"""
        responses = {}
        for agent in agents:
            try:
                response = agent.respond(topic, context, 1, stage, word_limits)
                responses[agent.name] = response
            except Exception as e:
                responses[agent.name] = f"[Error generating response: {e}]"
        return responses
