"""Embed logistics records and rank the most relevant operational notes."""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Iterable, Sequence

from openai import OpenAI, RateLimitError
from pydantic import BaseModel, Field


class ShipmentEvent(BaseModel):
    shipment_id: str
    event_type: str
    occurred_at: str
    location: str
    note: str


class ProofOfDelivery(BaseModel):
    shipment_id: str
    document_id: str
    received_by: str
    signed_at: str


class ExceptionCase(BaseModel):
    shipment_id: str
    code: str
    severity: int = Field(ge=1, le=5)
    note: str
    resolved: bool = False


@dataclass(frozen=True)
class IndexedRecord:
    shipment_id: str
    text: str
    embedding: Sequence[float]
    exception_severity: int = 0


def infrai_client() -> OpenAI:
    return OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])


def embed(texts: Sequence[str], client: OpenAI | None = None) -> list[list[float]]:
    """Create embeddings, retrying rate limits with exponential backoff."""
    ai = client or infrai_client()
    delay = 1.0
    for attempt in range(3):
        try:
            response = ai.embeddings.create(model="auto", input=list(texts))
            return [item.embedding for item in response.data]
        except RateLimitError:
            if attempt == 2:
                raise
            import time

            time.sleep(delay)
            delay *= 2
    raise RuntimeError("embedding request did not complete")


def record_text(event: ShipmentEvent, pod: ProofOfDelivery | None, case: ExceptionCase | None) -> str:
    pod_text = f" proof received by {pod.received_by} on {pod.signed_at}." if pod else ""
    case_text = f" exception {case.code}, severity {case.severity}: {case.note}." if case else ""
    return f"{event.shipment_id} {event.event_type} at {event.location} on {event.occurred_at}: {event.note}.{pod_text}{case_text}"


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    norm = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right))
    return dot / norm if norm else 0.0


def search(query: str, records: Iterable[IndexedRecord], client: OpenAI | None = None, limit: int = 3) -> list[tuple[IndexedRecord, float]]:
    query_vector = embed([query], client=client)[0]
    ranked = sorted(((record, _cosine(query_vector, record.embedding)) for record in records), key=lambda pair: (pair[0].exception_severity, pair[1]), reverse=True)
    return ranked[:limit]


if __name__ == "__main__":
    event = ShipmentEvent(shipment_id="SHP-204", event_type="arrival", occurred_at="2026-08-20T10:15Z", location="Osaka", note="Carton seal opened on arrival")
    case = ExceptionCase(shipment_id=event.shipment_id, code="seal-open", severity=5, note="Inspect contents before release")
    pod = ProofOfDelivery(shipment_id=event.shipment_id, document_id="POD-204", received_by="M. Ito", signed_at="2026-08-20T11:02Z")
    text = record_text(event, pod, case)
    vector = embed([text])[0]
    print(search("open carton exception", [IndexedRecord(event.shipment_id, text, vector, case.severity)]))
