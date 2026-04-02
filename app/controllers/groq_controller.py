import asyncio
import logging
import json
from groq import Groq
from sqlalchemy.ext.asyncio import AsyncSession
from app.controllers.base_controller import BaseController
from app.core.config import Settings

logger = logging.getLogger(__name__)

class GroqController(BaseController):
    def __init__(self, db: AsyncSession, settings: Settings):
        super().__init__(db, settings)
        self.client = Groq(api_key=self.settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def analyze_contract(self, text: str) -> dict:
        prompt = f"""
        You are a contract analyst. Analyze the following contract and return a JSON object with:
        1. summary: A brief 3-4 sentence summary
        2. contract_type: One of [employment, rental, freelance, nda, other]
        3. overall_risk_score: A score from 1-10 (10 being most risky)
        4. red_flags: A list of risky clauses found
        5. ip_clauses_score: Risk score 1-10
        6. termination_score: Risk score 1-10
        7. non_compete_score: Risk score 1-10
        8. payment_score: Risk score 1-10
        9. auto_renewal_score: Risk score 1-10

        Return ONLY a valid JSON object, no extra text.

        Contract:
        {text}
        """
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("Contract analysis completed")
        return self._parse_json(response.choices[0].message.content)

    async def answer_question(self, question: str, chunks: list, contract_name: str) -> dict:
        context = "\n\n".join([f"[{c.payload.get('section_title', 'Unknown')}]: {c.payload.get('text', '')}" for c in chunks])
        prompt = f"""
        You are a contract analyst protecting the user's interests.

        Analyze the question and context below and return a JSON object with:
        1. query_type: "risk" if the question involves termination, penalties, ownership, non-compete, auto-renewal, confidentiality, or anything that could harm the user. Otherwise "factual"
        2. answer: A detailed plain english answer based ONLY on the contract text provided
        3. sources: List of exact section titles used to answer
        4. risk_score: If query_type is "risk" give a score 1-10 (10 most risky), otherwise null
        5. risk_explanation: If query_type is "risk" explain exactly why it is risky, otherwise null

        Rules:
        - Always respond in the same language the question was asked in
        - If sources are in a different language translate them
        - Base your answer ONLY on the context provided, do not guess
        - Be specific and detailed in your answer
        - Always cite the exact section

        Contract name: {contract_name}
        Question: {question}

        Context:
        {context}

        Return ONLY a valid JSON object, no extra text.
        """
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("Question answered")
        return self._parse_json(response.choices[0].message.content)

    def _parse_json(self, text: str) -> dict:
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)