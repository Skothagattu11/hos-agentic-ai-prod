"""
Base Agent Framework for HolisticOS
Provides event-driven communication and shared functionality
"""

import asyncio
import json
import redis
import structlog
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from ..utils.system_prompts import get_system_prompt, get_archetype_adaptation

logger = structlog.get_logger()

class AgentEvent(BaseModel):
    """Event model for inter-agent communication"""
    event_id: str
    event_type: str
    source_agent: str
    target_agent: Optional[str] = None
    payload: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    archetype: Optional[str] = None

class AgentResponse(BaseModel):
    """Response model for agent processing"""
    response_id: str
    agent_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: datetime

class BaseAgent(ABC):
    """Base class for all HolisticOS agents with event-driven communication"""
    
    def __init__(self, agent_id: str, agent_type: str, redis_url: str = "redis://localhost:6379"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.pubsub = self.redis_client.pubsub()
        self.logger = logger.bind(agent_id=agent_id, agent_type=agent_type)
        
        # Get system prompt for this agent type
        self.system_prompt = get_system_prompt(agent_type)
        
        self.logger.debug("Agent initialized", system_prompt_length=len(self.system_prompt))
    
    async def publish_event(self, event_type: str, payload: Dict[str, Any], 
                          target_agent: Optional[str] = None, user_id: Optional[str] = None,
                          archetype: Optional[str] = None) -> None:
        """Publish an event to the event bus"""
        event = AgentEvent(
            event_id=f"{self.agent_id}_{datetime.now().timestamp()}",
            event_type=event_type,
            source_agent=self.agent_id,
            target_agent=target_agent,
            payload=payload,
            timestamp=datetime.now(),
            user_id=user_id,
            archetype=archetype
        )
        
        channel = f"events:{event_type}"
        if target_agent:
            channel = f"events:{target_agent}:{event_type}"
            
        await asyncio.to_thread(
            self.redis_client.publish,
            channel,
            event.model_dump_json()
        )
        
        self.logger.info("Event published", 
                        event_type=event_type, 
                        channel=channel,
                        target_agent=target_agent)
    
    async def subscribe_to_events(self, event_types: List[str], callback) -> None:
        """Subscribe to specific event types"""
        channels = []
        
        # Subscribe to general events
        for event_type in event_types:
            channels.append(f"events:{event_type}")
            
        # Subscribe to agent-specific events
        for event_type in event_types:
            channels.append(f"events:{self.agent_id}:{event_type}")
            
        await asyncio.to_thread(self.pubsub.subscribe, *channels)
        
        self.logger.info("Subscribed to events", channels=channels)
        
        # Listen for messages
        async for message in self._listen_for_messages():
            if message['type'] == 'message':
                try:
                    event_data = json.loads(message['data'])
                    event = AgentEvent.model_validate(event_data)
                    await callback(event)
                except Exception as e:
                    self.logger.error("Error processing event", error=str(e))
    
    async def _listen_for_messages(self):
        """Async generator for Redis pubsub messages"""
        while True:
            try:
                message = await asyncio.to_thread(self.pubsub.get_message, timeout=1.0)
                if message:
                    yield message
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                self.logger.error("Error listening for messages", error=str(e))
                await asyncio.sleep(1.0)
    
    def log_input_output(self, input_data: Dict[str, Any], output_data: Dict[str, Any], 
                        analysis_number: Optional[int] = None) -> None:
        """Log input and output data for debugging (preserve existing pattern)"""
        try:
            if analysis_number:
                input_file = f"input_{analysis_number}.txt"
                output_file = f"output_{analysis_number}.txt" 
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                input_file = f"input_{self.agent_id}_{timestamp}.txt"
                output_file = f"output_{self.agent_id}_{timestamp}.txt"
            
            # Log input data
            with open(input_file, 'w') as f:
                json.dump(input_data, f, indent=2, default=str)
            
            # Log output data 
            with open(output_file, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)
                
            self.logger.info("Input/output logged", 
                           input_file=input_file, 
                           output_file=output_file)
                           
        except Exception as e:
            self.logger.error("Error logging input/output", error=str(e))
    
    def get_archetype_guidance(self, archetype: str) -> str:
        """Get archetype-specific guidance for this agent"""
        return get_archetype_adaptation(archetype)
    
    @abstractmethod
    async def process(self, event: AgentEvent) -> AgentResponse:
        """Process an agent event - must be implemented by subclasses"""
        pass
    
    async def start_listening(self) -> None:
        """Start the agent's main listening loop"""
        event_types = self.get_supported_event_types()
        await self.subscribe_to_events(event_types, self.process)
    
    @abstractmethod
    def get_supported_event_types(self) -> List[str]:
        """Return list of event types this agent supports"""
        pass
    
    def __del__(self):
        """Cleanup Redis connections"""
        if hasattr(self, 'pubsub'):
            self.pubsub.close()
        if hasattr(self, 'redis_client'):
            self.redis_client.close()