"""Default prompt seeding for Helix.

Seeds default prompt templates with initial versions on fresh install.
Prompts are extracted from PALAI's retrieval_llm.py and adapted for Helix.
"""
import logging
from sqlalchemy.orm import Session

from database.models import PromptTemplate, PromptVersion

logger = logging.getLogger(__name__)


# Default prompt content
DEFAULT_PROMPTS = {
    "system_prompt": {
        "prompt_type": "system",
        "description": "Main system prompt for the chatbot",
        "content": """You are a helpful AI assistant. Your role is to provide accurate, helpful, and friendly responses to user questions.

Guidelines:
- Be concise and clear in your responses
- If you don't know something, admit it honestly
- Use the provided context to answer questions when available
- Be professional and respectful at all times
- Avoid making assumptions beyond what's stated in the context""",
    },
    "retrieval_prompt": {
        "prompt_type": "retrieval",
        "description": "RAG system prompt for answering with retrieved context",
        "content": """You are a helpful AI assistant. Answer the user's question based ONLY on the context provided below.

Context:
{context}

User Question: {question}

Instructions:
- Base your answer strictly on the context provided
- If the context doesn't contain enough information to answer the question, say so
- Be specific and cite relevant parts of the context
- Keep your answer clear and concise
- If multiple pieces of context are relevant, synthesize them into a coherent answer

Answer:""",
    },
}


def seed_default_prompts(db: Session) -> None:
    """Seed default prompt templates into the database.

    Creates prompt templates with initial versions if they don't already exist.
    This function is idempotent and safe to run multiple times.

    Args:
        db: SQLAlchemy database session.
    """
    logger.info("Seeding default prompts...")

    for name, config in DEFAULT_PROMPTS.items():
        # Check if prompt already exists
        existing = db.query(PromptTemplate).filter(
            PromptTemplate.name == name
        ).first()

        if existing:
            logger.info(f"Prompt '{name}' already exists, skipping...")
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
            created_by="system",
            change_notes="Initial default prompt",
        )
        db.add(version)

        logger.info(f"Created prompt template: {name}")

    db.commit()
    logger.info("Default prompts seeded successfully")
