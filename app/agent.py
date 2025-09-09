"""
Backward compatibility layer for the old agent interface.
This file now uses the unified core agent while maintaining the same API.
"""

import asyncio
from typing import Dict, Any
from .core_agent import get_agent, CoreAgent

# Backward compatibility - expose the graph from core agent
_agent_instance = None


def _get_agent() -> CoreAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = get_agent()
    return _agent_instance


# Expose graph for backward compatibility
class CompatibilityGraph:
    """Wrapper to maintain compatibility with existing code"""

    def __init__(self):
        self._agent = _get_agent()

    async def astream(self, inputs: Dict[str, Any]):
        """Async stream interface for backward compatibility"""
        question = inputs.get("question", "")
        result = await self._agent.process_question(question)

        # Yield result in the expected format
        yield {"agent": result}

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Sync invoke interface for backward compatibility"""
        question = inputs.get("question", "")

        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._agent.process_question(question))
        finally:
            loop.close()

        return result


# Legacy functions for backward compatibility
def get_answer(question: str) -> str:
    """Get answer using the unified core agent (sync interface)"""
    agent = _get_agent()

    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(agent.process_question(question))
        return result.get("generation", "Sorry, I couldn't process your question.")
    finally:
        loop.close()


async def get_answer_async(question: str) -> str:
    """Get answer using the unified core agent (async interface)"""
    agent = _get_agent()
    result = await agent.process_question(question)
    return result.get("generation", "Sorry, I couldn't process your question.")


# Export the compatibility graph
# This maintains the same interface as before while using the new core agent
graph = CompatibilityGraph()
