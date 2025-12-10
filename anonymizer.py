"""Core anonymization utilities using Stanza.

This module provides a simple API to load a Stanza pipeline and anonymize
English text by replacing named entity spans with bracketed labels, e.g.:
  "Barack Obama visited." -> "[PERSON] visited."
"""
from typing import List, Tuple, Optional
import threading
import os
import stanza

# Global pipeline cache to avoid re-loading models repeatedly.
_pipeline_lock = threading.Lock()
_stanza_pipeline: Optional[stanza.Pipeline] = None


def _ensure_pipeline() -> stanza.Pipeline:
    """
    Ensure a Stanza pipeline for English NER is available and loaded.

    Downloads the English models if needed.

    :returns: a loaded `stanza.Pipeline` with processors 'tokenize,ner'
    """
    global _stanza_pipeline
    with _pipeline_lock:
        if _stanza_pipeline is not None:
            return _stanza_pipeline

        # Prefer local model directory packaged alongside the app.
        model_dir = os.path.join(os.path.dirname(__file__), "stanza_models")
        # Attempt to download the english model into local model_dir if missing.
        try:
            stanza.download("en", processors="tokenize,ner", model_dir=model_dir, verbose=False)
        except Exception:
            # stanza.download may raise if already present or network is unavailable.
            # We'll attempt to create pipeline with available models.
            pass

        _stanza_pipeline = stanza.Pipeline(
            lang="en", processors="tokenize,ner", use_gpu=False, verbose=False, dir=model_dir
        )
        return _stanza_pipeline


def anonymize_with_stanza(text: str) -> str:
    """
    Anonymize named entities in `text` using Stanza.

    The function prefers Stanza's entity objects (`doc.ents`) and will
    replace each entity span with its label in square brackets, preserving
    surrounding text. If for some reason `doc.ents` is empty, a token-based
    BIO fallback is attempted.

    :param text: input English text
    :returns: anonymized text with entity spans replaced by `[LABEL]`
    """
    nlp = _ensure_pipeline()
    doc = nlp(text)

    def _spans_from_doc_ents(doc_obj) -> List[Tuple[int, int, str]]:
        spans_local: List[Tuple[int, int, str]] = []
        ents = getattr(doc_obj, "ents", None)
        if not ents:
            return spans_local
        for ent in ents:
            try:
                start = int(ent.start_char)
                end = int(ent.end_char)
                label = str(ent.type)
            except Exception:
                continue
            if start < end:
                spans_local.append((start, end, label))
        return spans_local

    def _spans_from_tokens(doc_obj) -> List[Tuple[int, int, str]]:
        spans_local: List[Tuple[int, int, str]] = []
        cur_start: Optional[int] = None
        cur_end: Optional[int] = None
        cur_type: Optional[str] = None

        for sent in getattr(doc_obj, "sentences", []):
            for token in getattr(sent, "tokens", []):
                ner_tag = getattr(token, "ner", "O")
                if ner_tag == "O":
                    if cur_start is not None and cur_end is not None and cur_type is not None:
                        spans_local.append((cur_start, cur_end, cur_type))
                    cur_start = cur_end = cur_type = None
                    continue

                parts = ner_tag.split("-")
                prefix = parts[0]
                ent_type = parts[-1]

                if prefix in ("B", "S", "U"):
                    if cur_start is not None and cur_end is not None and cur_type is not None:
                        spans_local.append((cur_start, cur_end, cur_type))
                    cur_start = token.start_char
                    cur_end = token.end_char
                    cur_type = ent_type
                    if prefix in ("S", "U"):
                        if cur_start is not None and cur_end is not None and cur_type is not None:
                            spans_local.append((cur_start, cur_end, cur_type))
                        cur_start = cur_end = cur_type = None
                elif prefix in ("I", "E", "L"):
                    if cur_type == ent_type and cur_start is not None:
                        cur_end = token.end_char
                        if prefix in ("E", "L"):
                            if cur_end is not None and cur_type is not None:
                                spans_local.append((cur_start, cur_end, cur_type))
                            cur_start = cur_end = cur_type = None
                    else:
                        spans_local.append((token.start_char, token.end_char, ent_type))
                        cur_start = cur_end = cur_type = None

            if cur_start is not None and cur_end is not None and cur_type is not None:
                spans_local.append((cur_start, cur_end, cur_type))
                cur_start = cur_end = cur_type = None

        return spans_local

    spans: List[Tuple[int, int, str]] = _spans_from_doc_ents(doc)
    if not spans:
        spans = _spans_from_tokens(doc)

    spans_sorted = sorted(spans, key=lambda x: x[0])
    result_parts: List[str] = []
    last_idx = 0
    for start, end, label in spans_sorted:
        if start >= end or start < last_idx:
            continue
        result_parts.append(text[last_idx:start])
        result_parts.append(f"[{label}]")
        last_idx = end
    result_parts.append(text[last_idx:])
    return "".join(result_parts)


if __name__ == "__main__":
    # Simple CLI for quick manual tests
    sample = "The Hubble Space Telescope orbits the Earth. It has provided stunning images of distant galaxies."
    print(anonymize_with_stanza(sample))
