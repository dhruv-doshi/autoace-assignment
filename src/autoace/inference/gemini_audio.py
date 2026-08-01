"""Approved Gemini audio boundary with fail-closed defaults.

The implementation deliberately does not make a request unless the caller
passes explicit approval and a cost projection. Provider SDK integration is
kept behind this boundary so local candidates remain usable without it.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autoace.inference.cost import CostPolicy, CostProjection


class RemoteApprovalRequired(RuntimeError):
    pass


class RemoteRouteUnavailable(RuntimeError):
    pass


def _normalize_observation(observation: object) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise RemoteRouteUnavailable("OpenRouter response must be a JSON object")
    normalized = dict(observation)
    noise_present = bool(normalized.get("background_noise_present", False))
    if not noise_present:
        normalized["background_noise_type"] = ""
        normalized["background_noise_severity"] = "none"
    else:
        if not str(normalized.get("background_noise_type", "")).strip():
            normalized["background_noise_type"] = "unclassified background noise"
        if normalized.get("background_noise_severity") == "none":
            normalized["background_noise_severity"] = "low"
    return normalized


@dataclass(frozen=True)
class RemoteApproval:
    approved: bool
    project_id: str | None
    endpoint: str | None
    region: str | None
    deletion_required: bool = True


class GeminiAudioObserver:
    def __init__(self, approval: RemoteApproval, cost_policy: CostPolicy) -> None:
        self.approval = approval
        self.cost_policy = cost_policy

    def preflight(self, projection: CostProjection) -> None:
        if not self.approval.approved:
            raise RemoteApprovalRequired("remote audio approval is not configured")
        if not self.approval.project_id or not self.approval.endpoint:
            raise RemoteApprovalRequired("remote project and endpoint are required")
        self.cost_policy.require_hard_compliance(projection)

    def observe(
        self,
        audio_path: Path,
        *,
        projection: CostProjection,
        prompt_version: str,
    ) -> dict[str, Any]:
        self.preflight(projection)
        if not audio_path.is_file():
            raise ValueError(f"audio file does not exist: {audio_path}")
        raise RemoteRouteUnavailable(
            "provider adapter is disabled until endpoint credentials and privacy "
            "approval are supplied"
        )


class OpenRouterAudioObserver:
    """OpenAI-compatible OpenRouter audio observer with an explicit spend cap."""

    def __init__(
        self,
        *,
        model: str = "google/gemini-3.5-flash-lite",
        budget_usd: float = 0.10,
        max_output_tokens: int = 256,
        instructions: str = "",
    ) -> None:
        self.model = model
        self.budget_usd = budget_usd
        self.max_output_tokens = max_output_tokens
        self.instructions = instructions.strip()
        self.spent_usd = 0.0
        self.base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.api_key = os.environ.get("OPENROUTER_API_KEY")
        self.prompt_version = "p4-openrouter-v2"

    def _prices(self) -> tuple[float, float]:
        prices = {
            "google/gemini-3.5-flash-lite": (0.30, 2.50),
            "google/gemini-3.6-flash": (1.50, 7.50),
        }
        return prices.get(self.model, prices["google/gemini-3.5-flash-lite"])

    def _wav_bytes(self, audio_path: Path) -> bytes:
        result = subprocess.run(
            [
                "ffmpeg", "-v", "error", "-i", str(audio_path), "-ac", "1", "-ar", "16000",
                "-f", "wav", "pipe:1",
            ],
            capture_output=True,
            check=False,
        )
        if result.returncode:
            raise ValueError(f"FFmpeg normalization failed: {result.stderr.decode()[:300]}")
        return result.stdout

    def _estimate_cost(self, audio_seconds: float) -> float:
        # Conservative planning estimate: 32 audio tokens/second plus prompt overhead.
        input_tokens = int(round(audio_seconds * 32)) + 2048
        input_price, output_price = self._prices()
        return (
            input_tokens * input_price / 1_000_000
            + self.max_output_tokens * output_price / 1_000_000
        )

    def _request_observation(
        self, payload: dict[str, Any], *, estimated_cost: float
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "http://localhost"),
                "X-Title": os.environ.get("OPENROUTER_APP_NAME", "AutoAce"),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_payload = json.load(response)
        except Exception as error:
            raise RemoteRouteUnavailable(f"OpenRouter request failed: {error}") from error
        content = response_payload["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(str(item.get("text", "")) for item in content)
        text = str(content).strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            observation = json.loads(text)
        except json.JSONDecodeError as error:
            raise RemoteRouteUnavailable(
                f"OpenRouter returned non-JSON output: {text[:300]}"
            ) from error
        observation = _normalize_observation(observation)
        usage = response_payload.get("usage", {})
        actual_cost = float(usage.get("cost") or estimated_cost)
        if self.spent_usd + actual_cost > self.budget_usd:
            raise RuntimeError("OpenRouter response exceeded the configured research budget")
        self.spent_usd += actual_cost
        return {
            "observation": observation,
            "model": self.model,
            "usage": usage,
            "estimated_cost_usd": estimated_cost,
            "actual_cost_usd": actual_cost,
            "spent_usd": self.spent_usd,
            "prompt_version": self.prompt_version,
        }

    def observe(self, audio_path: Path, *, audio_seconds: float) -> dict[str, Any]:
        if not self.api_key:
            raise RemoteRouteUnavailable("OPENROUTER_API_KEY is not configured")
        estimated = self._estimate_cost(audio_seconds)
        if self.spent_usd + estimated > self.budget_usd:
            raise RuntimeError("OpenRouter research budget exceeded before request")
        encoded = base64.b64encode(self._wav_bytes(audio_path)).decode("ascii")
        prompt = (
            "Analyze this customer-service call. Return only one JSON object with exactly "
            "these keys: emotional_tone (neutral|satisfied|frustrated|upset|distressed), "
            "emotional_intensity (low|medium|high), background_noise_present (boolean), "
            "background_noise_type (string), background_noise_severity (none|low|medium|high), "
            "audio_quality (clear|slightly_impaired|severely_impaired), "
            "speaker_overlap_present (boolean), long_silence_present (boolean), "
            "confidence (number 0 to 1). Focus on the customer, not the agent. "
            "Use medium for clearly noticeable but non-dominant noise; use TV only for "
            "audible programme/television audio and sharp static only for abrupt "
            "hiss/crackle/buzz. Mark speaker_overlap_present true only when two "
            "speakers are audible concurrently, even briefly. Treat repeated failed "
            "attempts to get a response as possible upset, and routine positive "
            "cooperation as satisfied only when the customer's delivery supports it."
        )
        if self.instructions:
            prompt = f"{prompt}\n\nAdditional rubric:\n{self.instructions}"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a careful call-audio evaluator."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "input_audio", "input_audio": {"data": encoded, "format": "wav"}},
                    ],
                },
            ],
            "temperature": 0,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        return self._request_observation(payload, estimated_cost=estimated)

    def adjudicate_text(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Adjudicate compact candidate evidence without uploading audio again."""

        if not self.api_key:
            raise RemoteRouteUnavailable("OPENROUTER_API_KEY is not configured")
        evidence_json = json.dumps(evidence, separators=(",", ":"))
        input_price, output_price = self._prices()
        estimated = (
            (len(evidence_json) // 4 + 1024) * input_price / 1_000_000
            + self.max_output_tokens * output_price / 1_000_000
        )
        if self.spent_usd + estimated > self.budget_usd:
            raise RuntimeError("OpenRouter research budget exceeded before request")
        prompt = (
            "Adjudicate the following call-analysis evidence. Return only a JSON object "
            "with the public call-analysis fields and a confidence from 0 to 1. Preserve "
            "a no-noise invariant: false requires empty type and severity none. Evidence: "
            f"{evidence_json}"
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a careful call-analysis adjudicator."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        self.prompt_version = "p7-openrouter-text-v1"
        return self._request_observation(payload, estimated_cost=estimated)
