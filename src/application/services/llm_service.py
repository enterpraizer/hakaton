import json

from google import genai
from google.genai import types

from src.infrastructure.scripts.generate_synthetic_data import SYNTHETIC_DATASET
from src.settings import settings

# 5 diverse few-shot examples (Web, DB, ML, CI/CD, Microservices)
_INDICES = [0, 10, 20, 30, 50]
FEW_SHOT_EXAMPLES = [SYNTHETIC_DATASET[i] for i in _INDICES]


def _few_shot_block() -> str:
    lines = ["Examples of correct configurations:"]
    for ex in FEW_SHOT_EXAMPLES:
        lines.append(
            f'  "{ex["description"]}" → {ex["vcpu"]} vCPU, {ex["ram_mb"]} MB RAM, {ex["disk_gb"]} GB disk'
        )
    return "\n".join(lines)


VM_CONFIG_SYSTEM = (
    "You are a cloud infrastructure expert. Given a workload description, "
    "suggest the optimal VM configuration.\n\n"
    + _few_shot_block()
    + "\n\nRespond ONLY with valid JSON matching exactly this schema (no markdown, no extra text):\n"
    '{"vcpu": int, "ram_mb": int, "disk_gb": int, "reasoning": str, "confidence": float}'
)

OPTIMIZATION_SYSTEM = (
    "You are a cloud infrastructure optimizer. Analyze the VM metrics for the last 7 days "
    "and suggest ONE optimization if needed. Be specific and actionable. "
    "Only suggest if confidence > 0.7.\n\n"
    "Respond ONLY with valid JSON matching exactly this schema (no markdown, no extra text):\n"
    '{"text": str, "confidence": float, "config": {"vcpu": int, "ram_mb": int, "disk_gb": int} or null}'
)

_GENERATE_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json",
    max_output_tokens=300,
    temperature=0.2,
)


def _default_config() -> dict:
    return {
        "vcpu": 2,
        "ram_mb": 2048,
        "disk_gb": 40,
        "reasoning": "Default configuration (LLM unavailable)",
        "confidence": 0.5,
    }


def _default_optimization() -> dict:
    return {"text": "No optimization needed", "confidence": 0.0, "config": None}


class LLMService:
    async def suggest_vm_config(self, description: str) -> dict:
        """
        Calls Gemini to suggest VM config based on workload description.
        Returns: {vcpu, ram_mb, disk_gb, reasoning, confidence}
        Falls back to defaults if API unavailable or disabled.
        """
        if not settings.llm.enabled or not settings.llm.gemini_api_key:
            return _default_config()

        try:
            client = genai.Client(api_key=settings.llm.gemini_api_key)
            response = await client.aio.models.generate_content(
                model=settings.llm.model,
                contents=description,
                config=types.GenerateContentConfig(
                    system_instruction=VM_CONFIG_SYSTEM,
                    response_mime_type="application/json",
                    max_output_tokens=300,
                    temperature=0.2,
                ),
            )
            return json.loads(response.text)
        except Exception:
            return _default_config()

    async def suggest_optimization(self, metrics_prompt: str) -> dict:
        """
        Analyzes VM metrics and suggests an optimization.
        Returns: {text, confidence, config (optional)}
        Falls back to no-op if API unavailable.
        """
        if not settings.llm.enabled or not settings.llm.gemini_api_key:
            return _default_optimization()

        try:
            client = genai.Client(api_key=settings.llm.gemini_api_key)
            response = await client.aio.models.generate_content(
                model=settings.llm.model,
                contents=metrics_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=OPTIMIZATION_SYSTEM,
                    response_mime_type="application/json",
                    max_output_tokens=300,
                    temperature=0.2,
                ),
            )
            return json.loads(response.text)
        except Exception:
            return _default_optimization()
