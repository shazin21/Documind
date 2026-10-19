import os
import re
from abc import ABC, abstractmethod
from typing import Optional
import httpx
from app.core.config import settings
from app.core.logging import logger


class BaseLLMProvider(ABC):
    """Abstract interface for LLM text generation."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str) -> str:
        """Generates grounded text completion given user prompt and system prompt."""
        pass


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic, offline LLM provider for reproducible tests and local evaluation.
    Answers directly from retrieved passages, adding citations [1], or states insufficient evidence.
    """

    def generate(self, prompt: str, system_prompt: str) -> str:
        # Check if prompt contains retrieved passages
        if "<retrieved_passages>" not in prompt or "No relevant passages found." in prompt:
            return "Based on the provided documents, there is insufficient evidence to answer this question."

        # Extract passages
        passages_text = prompt.split("<retrieved_passages>")[1].split("</retrieved_passages>")[0]
        # Extract user question
        question_match = re.search(r"User Question:\s*(.*)", prompt)
        question = question_match.group(1).strip() if question_match else ""

        # Extract individual passage entries
        passage_matches = re.findall(
            r"Passage \[(\d+)\] \([^)]+\):\s*(.*?)(?=(Passage \[\d+\]|</retrieved_passages>|$))",
            passages_text,
            re.DOTALL,
        )

        if not passage_matches:
            return "Based on the provided documents, there is insufficient evidence to answer this question."

        # Look for keywords from the question in passages
        keywords = [
            w.lower()
            for w in re.findall(r"\w+", question)
            if len(w) > 3 and w.lower() not in {"what", "where", "when", "which", "does", "have", "from", "with"}
        ]

        best_passage_idx = None
        best_sentence = ""
        max_matches = 0

        for p_idx, p_text, _ in passage_matches:
            sentences = re.split(r"(?<=[.!?])\s+", p_text.strip())
            for sent in sentences:
                matches = sum(1 for kw in keywords if kw in sent.lower())
                if matches > max_matches:
                    max_matches = matches
                    best_passage_idx = p_idx
                    best_sentence = sent.strip()

        if max_matches > 0 and best_passage_idx:
            # Clean sentence and attach citation
            clean_sent = re.sub(r"\s+", " ", best_sentence)
            return f"{clean_sent} [{best_passage_idx}]"
        elif len(passage_matches) > 0 and len(keywords) == 0:
            # Fallback for generic questions
            first_sent = passage_matches[0][1].strip().split("\n")[0]
            return f"{first_sent} [1]"
        else:
            return "Based on the provided documents, there is insufficient evidence to answer this question."


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API Provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = settings.GEMINI_MODEL,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name

    def generate(self, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError(
                "Gemini API key is not configured. Set GEMINI_API_KEY in .env or switch LLM_PROVIDER to 'mock'."
            )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_name}:generateContent?key={self.api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,  # Low temperature for deterministic grounded answers
                "maxOutputTokens": 1024,
            },
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise RuntimeError("No candidate text returned by Gemini.")
                return candidates[0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible API Provider (supports OpenAI, Groq, Ollama, DeepSeek, etc.)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = (
            api_key
            or settings.GROQ_API_KEY
            or settings.OPENAI_API_KEY
            or os.environ.get("GROQ_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )
        self.model_name = (
            model_name
            or (settings.GROQ_MODEL if settings.LLM_PROVIDER.lower() == "groq" else None)
            or settings.OPENAI_MODEL
        )
        raw_base = (
            base_url
            or (settings.GROQ_API_BASE if settings.LLM_PROVIDER.lower() == "groq" else None)
            or settings.OPENAI_BASE_URL
            or settings.OPENAI_API_BASE
            or os.environ.get("GROQ_API_BASE")
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("OPENAI_API_BASE")
            or "https://api.openai.com/v1"
        )
        self.base_url = raw_base.rstrip("/")

    def get_langchain_chat_model(self, temperature: float = 0.0):
        """Returns a LangChain-compatible ChatOpenAI instance pointing to this provider."""
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
        )

    def generate(self, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError(
                "LLM API key is not configured. Set GROQ_API_KEY or OPENAI_API_KEY in .env or switch LLM_PROVIDER to 'mock'."
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 1024,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"OpenAI/Groq API generation error: {e}")
            raise RuntimeError(f"LLM generation failed: {e}")


def get_llm_provider() -> BaseLLMProvider:
    provider_name = settings.LLM_PROVIDER.lower()
    if provider_name == "gemini":
        return GeminiProvider()
    elif provider_name in ("openai", "groq"):
        return OpenAIProvider()
    else:
        return MockLLMProvider()
