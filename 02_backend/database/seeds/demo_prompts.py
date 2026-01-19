"""Demo prompt seeding for Helix.

Seeds generic demo prompt templates for demo instances and sales demonstrations.
All prompts are generic and contain no domain-specific content.
"""
import logging
from sqlalchemy.orm import Session

from database.models import PromptTemplate, PromptVersion

logger = logging.getLogger(__name__)


# Demo prompt content - generic helpful assistant prompts
DEMO_PROMPTS = {
    "demo_system_prompt": {
        "prompt_type": "system",
        "description": "Generic demo system prompt for helpful assistant",
        "content": """You are a friendly and helpful AI assistant. Your role is to provide accurate, clear, and useful information to users.

Guidelines:
- Be polite, professional, and conversational
- Provide clear and concise answers
- If you don't know something, admit it honestly rather than guessing
- Ask clarifying questions when needed
- Use the context provided to give accurate answers
- Avoid making assumptions beyond what's stated
- Be respectful and inclusive in all interactions""",
    },
    "demo_retrieval_prompt": {
        "prompt_type": "retrieval",
        "description": "Generic demo RAG prompt for answering with retrieved context",
        "content": """You are a helpful AI assistant. Answer the user's question based ONLY on the information provided in the context below.

Context:
{context}

User Question: {question}

Instructions:
- Use only the information from the context above to answer
- If the context doesn't contain enough information, say "I don't have enough information to answer that question"
- Be specific and reference relevant parts of the context
- Keep your answer clear, concise, and easy to understand
- If multiple pieces of context are relevant, combine them into a coherent answer
- Don't add information that isn't in the context

Answer:""",
    },
    "demo_greeting_prompt": {
        "prompt_type": "greeting",
        "description": "Generic demo greeting response for new users",
        "content": """Hello! I'm here to help answer your questions.

I can assist you with information based on my knowledge base. Feel free to ask me anything, and I'll do my best to provide accurate and helpful answers.

What would you like to know?""",
    },
    "demo_fallback_prompt": {
        "prompt_type": "fallback",
        "description": "Generic demo fallback response when unable to help",
        "content": """I apologize, but I don't have enough information to answer that question accurately.

Here's what you can try:
- Rephrase your question with more details
- Ask about a different topic
- Contact support for assistance with specific issues

Is there anything else I can help you with?""",
    },
}


def seed_demo_prompts(db: Session) -> None:
    """Seed demo prompt templates into the database.

    Creates generic demo prompt templates with initial versions.
    These prompts are designed for demo instances and contain no
    domain-specific content.

    This function is idempotent and safe to run multiple times.

    Args:
        db: SQLAlchemy database session.
    """
    logger.info("Seeding demo prompts...")

    for name, config in DEMO_PROMPTS.items():
        # Check if prompt already exists
        existing = db.query(PromptTemplate).filter(
            PromptTemplate.name == name
        ).first()

        if existing:
            logger.info(f"Demo prompt '{name}' already exists, skipping...")
            continue

        # Create template
        template = PromptTemplate(
            name=name,
            prompt_type=config["prompt_type"],
            description=config["description"],
        )
        db.add(template)
        db.flush()  # Get ID for version

        # Create initial version
        version = PromptVersion(
            template_id=template.id,
            content=config["content"],
            version_number=1,
            is_active=True,
            created_by="demo_seed",
            change_notes="Initial demo prompt for demonstration purposes",
        )
        db.add(version)

        logger.info(f"Created demo prompt template: {name}")

    db.commit()
    logger.info("Demo prompts seeded successfully")
