import json
import logging
import httpx
from src.controllers.LLM.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def call(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False}
            )
            response.raise_for_status()
            return response.json()["response"]

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
        raw = await self.call(prompt)
        logger.info("Ollama: contract analysis completed")
        return parse_json(raw)

    async def answer_question(self, question: str, chunks: list, contract_name: str) -> dict:
        context = "\n\n".join([
            f"[{c.payload.get('section_title', 'Unknown')}]: {c.payload.get('text', '')}"
            for c in chunks
        ])
        prompt = f"""
        You are a contract analyst protecting the user's interests.
        Return a JSON object with query_type, answer, sources, risk_score, risk_explanation.
        Base your answer ONLY on the context. Return ONLY valid JSON.

        Contract name: {contract_name}
        Question: {question}
        Context: {context}
        """
        raw = await self.call(prompt)
        logger.info("Ollama: question answered")
        return parse_json(raw)


def parse_json(text: str) -> dict:
    clean = text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)