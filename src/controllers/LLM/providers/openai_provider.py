import json
import logging
from openai import AsyncOpenAI
from src.controllers.LLM.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

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
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("OpenAI: contract analysis completed")
        return parse_json(response.choices[0].message.content)

    async def answer_question(self, question: str, chunks: list, contract_name: str) -> dict:
        context = "\n\n".join([
            f"[{c.payload.get('section_title', 'Unknown')}]: {c.payload.get('text', '')}"
            for c in chunks
        ])
        prompt = f"""
        You are a contract analyst protecting the user's interests.

        Analyze the question and context below and return a JSON object with:
        1. query_type: "risk" or "factual"
        2. answer: Detailed answer based ONLY on the contract text
        3. sources: List of exact section titles used
        4. risk_score: 1-10 if risk, otherwise null
        5. risk_explanation: Explanation if risk, otherwise null

        Rules:
        - Respond in the same language as the question
        - Base answer ONLY on context provided
        - Always cite the exact section

        Contract name: {contract_name}
        Question: {question}
        Context: {context}

        Return ONLY a valid JSON object, no extra text.
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("OpenAI: question answered")
        return parse_json(response.choices[0].message.content)


def parse_json(text: str) -> dict:
    clean = text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)