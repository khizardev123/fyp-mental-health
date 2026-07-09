"""Word-based mouth timing estimation (lip-sync placeholder)."""

import re


def estimate_mouth_timings(text: str) -> dict:
    clean = (text or "").strip()
    words = re.findall(r"\S+", clean)
    if not words:
        return {"total_duration_ms": 0, "timings": [], "words_per_second": 2.5}

    # ~280ms per word average speaking pace
    ms_per_word = 280
    timings = []
    cursor = 0

    for word in words:
        # Longer words = slightly longer mouth open
        open_amount = min(1.0, 0.55 + len(word) * 0.04)
        start = cursor
        end = cursor + ms_per_word
        timings.append({
            "word": word,
            "start_ms": start,
            "end_ms": end,
            "mouth_open": round(open_amount, 2),
        })
        cursor = end

    return {
        "total_duration_ms": cursor,
        "timings": timings,
        "words_per_second": round(1000 / ms_per_word, 2),
    }
