"""Structured timing for the SereneMind chat response pipeline."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from time import perf_counter
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PipelineTiming:
    message_received_ms: float = 0.0
    db_session_ms: float = 0.0
    intent_detection_ms: float = 0.0
    ml_analysis_ms: float = 0.0
    pinecone_embed_ms: float = 0.0
    pinecone_query_ms: float = 0.0
    memory_filtering_ms: float = 0.0
    emotion_rules_ms: float = 0.0
    prompt_construction_ms: float = 0.0
    save_user_message_ms: float = 0.0
    prep_total_ms: float = 0.0
    meta_emitted_ms: float = 0.0
    ollama_probe_ms: float = 0.0
    ollama_ttft_ms: float = 0.0
    ollama_generation_ms: float = 0.0
    streaming_ms: float = 0.0
    save_assistant_ms: float = 0.0
    summary_update_ms: float = 0.0
    avatar_emotion_ms: float = 0.0
    total_ms: float = 0.0
    # Client-side (filled by frontend, echoed in done payload when present)
    tts_generation_ms: float = 0.0
    audio_playback_start_ms: float = 0.0
    client_total_ms: float = 0.0

    _marks: dict[str, float] = field(default_factory=dict, repr=False)

    def mark(self, name: str) -> None:
        self._marks[name] = perf_counter()

    def since(self, name: str) -> float:
        start = self._marks.get(name)
        if start is None:
            return 0.0
        return (perf_counter() - start) * 1000

    def to_dict(self) -> dict[str, Any]:
        return {k: round(v, 1) for k, v in asdict(self).items() if k != "_marks"}

    def format_breakdown(self) -> str:
        pinecone_total = self.pinecone_embed_ms + self.pinecone_query_ms + self.memory_filtering_ms
        lines = [
            ("Message received", self.message_received_ms),
            ("ML analysis", self.ml_analysis_ms),
            ("Intent detection", self.intent_detection_ms),
            ("Pinecone retrieval", pinecone_total),
            ("  embed", self.pinecone_embed_ms),
            ("  query", self.pinecone_query_ms),
            ("  filter", self.memory_filtering_ms),
            ("Prompt construction", self.prompt_construction_ms),
            ("Prep total (pre-stream)", self.prep_total_ms),
            ("Meta emitted", self.meta_emitted_ms),
            ("Ollama probe", self.ollama_probe_ms),
            ("Ollama TTFT", self.ollama_ttft_ms),
            ("Ollama generation", self.ollama_generation_ms),
            ("Streaming", self.streaming_ms),
            ("Save assistant", self.save_assistant_ms),
            ("Summary update", self.summary_update_ms),
            ("Avatar emotion", self.avatar_emotion_ms),
            ("TTS generation", self.tts_generation_ms),
            ("Audio playback start", self.audio_playback_start_ms),
            ("Total response", self.total_ms),
        ]
        width = max(len(label) for label, _ in lines)
        body = "\n".join(f"{label:<{width}} .... {ms:>7.1f} ms" for label, ms in lines)
        return f"[Pipeline Timing]\n{body}"


def log_pipeline_timing(timing: PipelineTiming) -> None:
    logger.info(timing.format_breakdown())
