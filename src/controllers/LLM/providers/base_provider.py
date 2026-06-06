from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):

    @abstractmethod
    async def analyze_contract(self, text: str) -> dict:
        pass

    @abstractmethod
    async def answer_question(self, question: str, chunks: list, contract_name: str) -> dict:
        pass