"""
Core constants for Helix.

This module defines enums and constants used throughout the application.
"""
from enum import Enum
from typing import List


class PromptType(str, Enum):
    """Enumeration of valid prompt types.

    Each prompt template must have one of these types. This ensures
    consistency across the system and enables type-safe prompt retrieval.

    Attributes:
        SYSTEM_PROMPT: Main system prompt for chatbot persona.
        GREETING: Initial greeting for new users.
        FAREWELL: Farewell message when ending conversation.
        REJECTION: Response when query cannot be answered.
        CLARIFICATION: Prompt for clarifying ambiguous queries.
        HANDOFF: Message for human handoff scenarios.
        RETRIEVAL: RAG system prompt for context retrieval.
        FALLBACK: Default response when other processing fails.
    """

    SYSTEM_PROMPT = "system_prompt"
    GREETING = "greeting"
    FAREWELL = "farewell"
    REJECTION = "rejection"
    CLARIFICATION = "clarification"
    HANDOFF = "handoff"
    RETRIEVAL = "retrieval"
    FALLBACK = "fallback"

    @classmethod
    def is_valid_type(cls, value: str) -> bool:
        """Check if a string is a valid prompt type.

        Args:
            value: String to check.

        Returns:
            True if value is a valid prompt type, False otherwise.
        """
        return value in [t.value for t in cls]

    @classmethod
    def get_all_types(cls) -> List[str]:
        """Get list of all valid prompt type values.

        Returns:
            List of prompt type string values.
        """
        return [t.value for t in cls]


# Default prompt content for fallback scenarios
DEFAULT_PROMPTS = {
    PromptType.SYSTEM_PROMPT: (
        "You are a helpful AI assistant. Answer questions accurately "
        "and concisely based on the provided context."
    ),
    PromptType.GREETING: "Hello! How can I help you today?",
    PromptType.FAREWELL: "Goodbye! Feel free to return if you have more questions.",
    PromptType.REJECTION: (
        "I'm sorry, but I cannot help with that request. "
        "Please ask something related to our knowledge base."
    ),
    PromptType.CLARIFICATION: (
        "I'm not sure I understand your question. "
        "Could you please provide more details?"
    ),
    PromptType.HANDOFF: (
        "I'll connect you with a human representative who can better assist you."
    ),
    PromptType.RETRIEVAL: (
        "Use the following context to answer the user's question. "
        "If the answer is not in the context, say you don't know.\n\n"
        "Context: {context}\n\nQuestion: {question}"
    ),
    PromptType.FALLBACK: (
        "I apologize, but I'm having trouble processing your request right now. "
        "Please try again later."
    ),
}
