# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/greeter.py
# PURPOSE: Simple test agent to verify CrewAI is working
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent
import os

def create_greeter_agent():
    """
    Create a simple conversational agent for testing.
    
    WHAT: Creates a friendly AI agent that can chat
    WHY: To verify CrewAI + OpenAI integration works
    HOW: Uses CrewAI's Agent class with OpenAI model
    """
    
    agent = Agent(
        role="Friendly Assistant",
        goal="Have helpful and friendly conversations",
        backstory="You are a helpful AI assistant who loves to chat and help people.",
        verbose=True,
        allow_delegation=False,
        llm="gpt-4o-mini"  # Using the affordable model
    )
    
    return agent