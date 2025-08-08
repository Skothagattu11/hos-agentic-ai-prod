"""
Unit tests for system prompts
"""
import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from shared_libs.utils.system_prompts import (
    get_system_prompt, 
    get_archetype_adaptation, 
    AGENT_PROMPTS
)

class TestSystemPrompts:
    """Test system prompt functionality"""
    
    def test_universal_prompt_exists(self):
        """Test that universal prompt is available"""
        universal_prompt = get_system_prompt("universal")
        assert len(universal_prompt) > 0
        assert "HolisticOS ecosystem" in universal_prompt
    
    def test_behavior_agent_prompt(self):
        """Test behavior analysis agent prompt"""
        prompt = get_system_prompt("behavior_analysis")
        assert len(prompt) > 0
        assert "behavioral intelligence core" in prompt
        assert "HolisticOS ecosystem" in prompt  # Should include universal prompt
    
    def test_plan_generation_prompt(self):
        """Test plan generation agent prompt"""
        prompt = get_system_prompt("plan_generation")
        assert len(prompt) > 0
        assert "creative intelligence" in prompt
    
    def test_memory_management_prompt(self):
        """Test memory management agent prompt"""
        prompt = get_system_prompt("memory_management")
        assert len(prompt) > 0
        assert "learning intelligence" in prompt
    
    def test_archetype_adaptations(self):
        """Test archetype-specific adaptations"""
        peak_performer = get_archetype_adaptation("Peak Performer")
        assert len(peak_performer) > 0
        assert "optimization" in peak_performer.lower()
        
        foundation_builder = get_archetype_adaptation("Foundation Builder")
        assert len(foundation_builder) > 0
        assert "simple" in foundation_builder.lower()
    
    def test_unknown_agent_type(self):
        """Test handling of unknown agent types"""
        prompt = get_system_prompt("unknown_agent")
        # Should return just the universal prompt
        assert len(prompt) > 0
        assert prompt == AGENT_PROMPTS["universal"]
    
    def test_unknown_archetype(self):
        """Test handling of unknown archetypes"""
        adaptation = get_archetype_adaptation("Unknown Archetype")
        assert adaptation == ""

if __name__ == "__main__":
    pytest.main([__file__])