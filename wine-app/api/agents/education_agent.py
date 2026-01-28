"""
Education Agent for wine knowledge questions.
Handles both general wine education and specific wine queries.
"""

from typing import Optional, Dict, Any, List
from openai import OpenAI
from sqlalchemy.orm import Session

from config import Config
from models.database import Wine
from utils.embeddings import search_wset_knowledge


class EducationAgent:
    """
    Agent for handling wine education queries.
    Uses WSET knowledge base for general questions and catalog data for specific wines.
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    def answer_general(self, question: str) -> Dict[str, Any]:
        """
        Answer a general wine education question using WSET knowledge.

        Args:
            question: User's wine question

        Returns:
            Dict with 'answer' and 'sources'
        """
        # Search WSET knowledge base
        try:
            knowledge_chunks = search_wset_knowledge(question, top_k=3)
        except Exception as e:
            print(f"WSET search error: {e}")
            knowledge_chunks = []

        if not knowledge_chunks:
            return {
                "answer": self._generate_fallback_answer(question),
                "sources": [],
                "confidence": 0.5
            }

        # Build context from retrieved chunks
        context_parts = []
        sources = []
        for chunk in knowledge_chunks:
            context_parts.append(f"**{chunk['heading']}**\n{chunk['text']}")
            sources.append({
                "heading": chunk['heading'],
                "relevance": chunk['score']
            })

        knowledge_context = "\n\n".join(context_parts)

        # Generate answer
        prompt = f"""You are Pip, a wine expert trained in WSET wine knowledge.
Answer the user's question using the knowledge context provided.

RULES:
- Be informative but conversational
- Use the WSET knowledge provided, but explain in accessible terms
- DO NOT recommend specific wines - this is an educational response only
- Keep response focused and under 3 paragraphs
- If the context doesn't fully answer the question, acknowledge what you do know

WSET Knowledge Context:
{knowledge_context}

User Question: {question}

Respond as Pip, the friendly wine mentor."""

        answer = self._generate_response(prompt)

        return {
            "answer": answer,
            "sources": sources,
            "confidence": max(chunk['score'] for chunk in knowledge_chunks) if knowledge_chunks else 0.5
        }

    def answer_specific(
        self,
        wine_id: Optional[str] = None,
        wine_name: Optional[str] = None,
        question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a question about a specific wine.

        Args:
            wine_id: Optional wine ID from catalog
            wine_name: Optional wine name for search
            question: User's question about the wine

        Returns:
            Dict with 'answer', 'wine_details', and 'found'
        """
        wine = None

        # Try to find the wine
        if wine_id:
            wine = self.db.query(Wine).filter(Wine.id == wine_id).first()

        if not wine and wine_name:
            # Search by name
            wine = self.db.query(Wine).filter(
                Wine.name.ilike(f"%{wine_name}%")
            ).first()

        if not wine:
            return {
                "answer": f"I don't have specific details about that wine in my catalog. If you tell me more about it (producer, region, grape variety), I can share general knowledge about wines like that.",
                "wine_details": None,
                "found": False
            }

        # Build wine details
        wine_details = {
            "id": wine.id,
            "name": wine.name,
            "producer": wine.producer,
            "vintage": wine.vintage,
            "wine_type": wine.wine_type,
            "varietal": wine.varietal,
            "region": wine.region,
            "country": wine.country,
            "price_usd": wine.price_usd
        }

        metadata = wine.wine_metadata or {}
        wine_details.update({
            "body": metadata.get("body"),
            "sweetness": metadata.get("sweetness"),
            "acidity": metadata.get("acidity"),
            "tannin": metadata.get("tannin"),
            "characteristics": metadata.get("characteristics", []),
            "flavor_notes": metadata.get("flavor_notes", [])
        })

        # Generate response
        details_text = f"""
Wine: {wine.name}
Producer: {wine.producer or 'Unknown'}
Vintage: {wine.vintage or 'NV'}
Type: {wine.wine_type}
Varietal: {wine.varietal or 'Blend'}
Region: {wine.region or 'Unknown'}, {wine.country or ''}
Price: ${wine.price_usd or 'N/A'}
Body: {metadata.get('body', 'N/A')}
Characteristics: {', '.join(metadata.get('characteristics', [])) or 'N/A'}
Flavor Notes: {', '.join(metadata.get('flavor_notes', [])) or 'N/A'}
"""

        user_question = question or "Tell me about this wine"

        prompt = f"""You are Pip, a wine expert. The user is asking about a specific wine.

Wine Details:
{details_text}

User Question: {user_question}

Provide helpful information about this wine. Cover:
- What makes this wine special or notable
- Tasting profile and what to expect
- Food pairing suggestions
- When to drink it (is it ready now or should it age?)

Keep it conversational and informative."""

        answer = self._generate_response(prompt)

        return {
            "answer": answer,
            "wine_details": wine_details,
            "found": True
        }

    def explain_term(self, term: str) -> str:
        """
        Explain a wine term or concept.

        Args:
            term: Wine term to explain (e.g., "tannins", "malolactic fermentation")

        Returns:
            Explanation string
        """
        # First try WSET knowledge
        result = self.answer_general(f"What is {term} in wine?")
        return result["answer"]

    def compare_wines(
        self,
        wine1_name: str,
        wine2_name: str
    ) -> Dict[str, Any]:
        """
        Compare two wines or wine styles.

        Args:
            wine1_name: First wine or style
            wine2_name: Second wine or style

        Returns:
            Comparison dict with explanation
        """
        # Search for both wines
        wine1 = self.db.query(Wine).filter(
            Wine.name.ilike(f"%{wine1_name}%") |
            Wine.varietal.ilike(f"%{wine1_name}%")
        ).first()

        wine2 = self.db.query(Wine).filter(
            Wine.name.ilike(f"%{wine2_name}%") |
            Wine.varietal.ilike(f"%{wine2_name}%")
        ).first()

        # Also get WSET knowledge for the comparison
        comparison_query = f"difference between {wine1_name} and {wine2_name} wine"
        knowledge_result = self.answer_general(comparison_query)

        return {
            "comparison": knowledge_result["answer"],
            "wine1_found": wine1 is not None,
            "wine2_found": wine2 is not None
        }

    def _generate_response(self, prompt: str) -> str:
        """Generate a response using the LLM."""
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are Pip, a friendly and knowledgeable wine mentor."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return "I'm having trouble generating a response right now. Please try again."

    def _generate_fallback_answer(self, question: str) -> str:
        """Generate an answer without specific knowledge context."""
        prompt = f"""You are Pip, a wine expert. Answer this wine question to the best of your knowledge.
Be honest if you're not certain about something.

Question: {question}

Provide a helpful, educational response."""

        return self._generate_response(prompt)
