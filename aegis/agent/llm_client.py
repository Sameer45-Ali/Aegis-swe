"""
Unified LLM Client Supporting Groq, OpenAI, Anthropic, Ollama, and Dynamic Smart Mock.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
import httpx
from aegis.config import settings


class LLMClient:
    """Manages calls to LLM backends with structured JSON extraction and fallback support."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        self.groq_api_key = os.getenv("GROQ_API_KEY") or settings.groq_api_key
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY") or settings.anthropic_api_key
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL") or settings.ollama_base_url

    async def generate_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        raw_text = await self.generate_text(prompt, system_prompt)
        clean = raw_text.strip()
        if "```json" in clean:
            match = re.search(r"```json\s*(.*?)\s*```", clean, re.DOTALL)
            if match:
                clean = match.group(1)
        elif "```" in clean:
            match = re.search(r"```\s*(.*?)\s*```", clean, re.DOTALL)
            if match:
                clean = match.group(1)

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r"(\{.*\})", clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            return {"raw_response": raw_text, "error": "JSON parse failed"}

    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        if self.provider == "groq" and self.groq_api_key:
            return await self._call_groq(prompt, system_prompt)
        elif self.provider == "openai" and self.openai_api_key:
            return await self._call_openai(prompt, system_prompt)
        elif self.provider == "anthropic" and self.anthropic_api_key:
            return await self._call_anthropic(prompt, system_prompt)
        elif self.provider == "ollama":
            return await self._call_ollama(prompt, system_prompt)
        else:
            return self._mock_response(prompt)

    async def _call_groq(self, prompt: str, system_prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model or "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_openai(self, prompt: str, system_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model or "gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 4096,
            "temperature": 0.2
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.model or "llama3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": "json"
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["message"]["content"]

    def _mock_response(self, prompt: str) -> str:
        """Deterministic smart response for offline testing."""
        prompt_lower = prompt.lower()
        if "math_helper.py" in prompt_lower or "divide_numbers" in prompt_lower or "get_full_name" in prompt_lower:
            if "reproduces the bug" in prompt_lower or "repro_issue" in prompt_lower:
                return json.dumps({
                    "test_file_path": "tests/test_repro_math.py",
                    "test_code": (
                        "from math_helper import divide_numbers, get_full_name\n\n"
                        "def test_division_by_zero():\n"
                        "    assert divide_numbers(10, 0) == 0\n\n"
                        "def test_none_names():\n"
                        "    assert get_full_name(None, 'Ali') == 'Ali'\n"
                        "    assert get_full_name('Sameer', None) == 'Sameer'\n"
                    ),
                    "rationale": "Asserts divide by zero returns 0 and None names are handled safely."
                })
            else:
                return json.dumps({
                    "target_file": "math_helper.py",
                    "updated_content": (
                        "def divide_numbers(a, b):\n"
                        "    if b == 0:\n"
                        "        return 0\n"
                        "    return a / b\n\n\n"
                        "def get_full_name(first, last):\n"
                        "    first_clean = first or ''\n"
                        "    last_clean = last or ''\n"
                        "    return f\"{first_clean} {last_clean}\".strip()\n"
                    ),
                    "explanation": "Added zero check for b == 0 and safe string formatting handling None values."
                })
        elif "metrics.py" in prompt_lower or "calculate_conversion_funnel" in prompt_lower or "retention" in prompt_lower:
            if "reproduces the bug" in prompt_lower or "repro_issue" in prompt_lower:
                return json.dumps({
                    "test_file_path": "tests/test_repro_metrics.py",
                    "test_code": (
                        "import pytest\n"
                        "from analytics.metrics import calculate_conversion_funnel, calculate_retention_rate\n\n"
                        "def test_funnel_zero_division():\n"
                        "    stages = {'impressions': 100, 'clicks': 0, 'purchases': 0}\n"
                        "    res = calculate_conversion_funnel(stages)\n"
                        "    assert res['clicks_to_purchases'] == 0.0\n\n"
                        "def test_negative_cohort_raises_error():\n"
                        "    with pytest.raises(ValueError):\n"
                        "        calculate_retention_rate(['u1'], ['u1'], -5)\n"
                    ),
                    "rationale": "Tests ZeroDivisionError when middle funnel stage count is 0."
                })
            else:
                return json.dumps({
                    "target_file": "analytics/metrics.py",
                    "updated_content": (
                        "def calculate_retention_rate(active_users: list, returning_users: list, cohort_size: int) -> float:\n"
                        "    if cohort_size < 0:\n"
                        "        raise ValueError('Cohort size must be non-negative')\n"
                        "    if cohort_size == 0:\n"
                        "        return 0.0\n"
                        "    \n"
                        "    unique_active = set(active_users)\n"
                        "    unique_returning = set(returning_users)\n"
                        "    retained = unique_active.intersection(unique_returning)\n"
                        "    \n"
                        "    rate = (len(retained) / cohort_size) * 100.0\n"
                        "    return round(rate, 2)\n\n\n"
                        "def calculate_conversion_funnel(stages: dict) -> dict:\n"
                        "    if not stages:\n"
                        "        return {}\n"
                        "    \n"
                        "    stage_keys = list(stages.keys())\n"
                        "    conversion_rates = {}\n"
                        "    \n"
                        "    for i in range(len(stage_keys) - 1):\n"
                        "        curr_stage = stage_keys[i]\n"
                        "        next_stage = stage_keys[i + 1]\n"
                        "        \n"
                        "        curr_count = stages[curr_stage]\n"
                        "        next_count = stages[next_stage]\n"
                        "        \n"
                        "        if curr_count == 0:\n"
                        "            dropoff_pct = 0.0\n"
                        "        else:\n"
                        "            dropoff_pct = ((curr_count - next_count) / curr_count) * 100.0\n"
                        "        conversion_rates[f\"{curr_stage}_to_{next_stage}\"] = round(dropoff_pct, 2)\n"
                        "        \n"
                        "    return conversion_rates\n"
                    ),
                    "explanation": "Added zero-division guard check for curr_count == 0."
                })
        else:
            return json.dumps({
                "test_file_path": "tests/test_generic.py",
                "test_code": "def test_ok(): assert True",
                "target_file": "module.py",
                "updated_content": "# Clean patch\n",
                "explanation": "Generic fix"
            })