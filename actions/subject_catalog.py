"""Runtime access to the authoritative subject catalog."""

from __future__ import annotations

import time
from typing import Callable, List, Dict, Any


class SubjectCatalogRepository:
    """Fetch and cache the canonical ``Materia`` catalog in memory."""

    def __init__(self, client, ttl_seconds: float = 600, clock: Callable[[], float] | None = None):
        self._client = client
        self._ttl_seconds = ttl_seconds
        self._clock = clock or time.monotonic
        self._cached_subjects: List[Dict[str, Any]] | None = None
        self._cached_at: float | None = None
        self._cached_client_id: int | None = None

    def _client_instance(self):
        return self._client() if callable(self._client) else self._client

    def get_subjects(self) -> List[Dict[str, Any]]:
        now = self._clock()
        client = self._client_instance()
        if (
            self._cached_subjects is not None
            and self._cached_at is not None
            and self._cached_client_id == id(client)
            and now - self._cached_at < self._ttl_seconds
        ):
            return list(self._cached_subjects)

        response = (
            client
            .table("Materia")
            .select("codigo, nombre")
            .execute()
        )
        subjects = [
            {"codigo": row.get("codigo"), "nombre": row.get("nombre")}
            for row in (response.data or [])
            if row.get("codigo") is not None and row.get("nombre")
        ]
        self._cached_subjects = subjects
        self._cached_at = now
        self._cached_client_id = id(client)
        return list(subjects)
