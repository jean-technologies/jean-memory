import logging
from app.database import SessionLocal
from app.models import Memory
import openai
import os
import json
import re
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

async def extract_and_store_entities(db: Session, memory_id: str):
    """
    Asynchronously extracts entities from a memory's content and stores them.
    Accepts a database session to prevent connection pooling issues.
    """
    try:
        memory = db.query(Memory).filter(Memory.id == memory_id).first()
        if not memory or not memory.content:
            logger.warning(f"Memory not found or has no content: {memory_id}")
            return

        # Use the same Custom Fact Extraction Prompt as Jean Memory V2 ingestion
        fact_extraction_prompt = """
Please extract structured facts about entities and their relationships from the provided text.
Focus on extracting entities of types: Person, Place, Event, Topic, Object, Emotion.

Entity types to extract:
1. Person: Names, ages, occupations, locations, relationships, roles
2. Place: Locations, addresses, place types, descriptions, buildings
3. Event: Activities, meetings, experiences, occurrences, milestones
4. Topic: Subjects, interests, categories, themes, skills
5. Object: Items, products, belongings, purchases, tools
6. Emotion: Feelings, moods, emotional states, reactions

Return the extracted facts in JSON format:
{
    "facts": [
        "Person: [name]",
        "Person: [name] - [attribute]: [value]",
        "Place: [name]",
        "Place: [name] - [attribute]: [value]",
        "Event: [name]",
        "Event: [name] - [attribute]: [value]",
        "Topic: [name]",
        "Object: [name]",
        "Emotion: [name]"
    ]
}
"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("OpenAI API key not available")
        
        openai_client = openai.AsyncOpenAI(api_key=api_key)
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": fact_extraction_prompt},
                {"role": "user", "content": memory.content[:1500]}
            ],
            temperature=0.1,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        if not content:
            return

        fact_data = {}
        try:
            if content.startswith('{') and content.endswith('}'):
                fact_data = json.loads(content)
            else:
                json_match = re.search(r'\{[^}]*"facts"[^}]*\}', content, re.DOTALL)
                if json_match:
                    fact_data = json.loads(json_match.group())
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from GPT response for memory {memory.id}: {e}")
            return

        facts = fact_data.get('facts', [])
        if facts:
            memory.entities = {"entities": facts}
            db.commit()
            logger.info(f"Successfully extracted and stored {len(facts)} entities for memory {memory.id}")

    except Exception as e:
        logger.error(f"Entity extraction failed for memory {memory_id}: {e}", exc_info=True)
        db.rollback()
    # The session is managed by the calling function, so we don't close it here. 