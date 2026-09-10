"""Pure subject-expression normalization and catalog resolution."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List


def normalize_subject(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(without_marks.casefold().split())


def _roman_to_int(token: str):
    if not re.fullmatch(r"[ivxlcdm]+", token):
        return None
    values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    total = 0
    previous = 0
    for char in reversed(token):
        value = values[char]
        total += -value if value < previous else value
        previous = value
    return total if total > 0 else None


def subject_parts(value: str):
    normalized = normalize_subject(value)
    tokens = normalized.split()
    if not tokens:
        return "", None
    final = tokens[-1]
    if final.isdigit() and int(final) > 0:
        return " ".join(tokens[:-1]), int(final)
    roman = _roman_to_int(final)
    if roman is not None:
        return " ".join(tokens[:-1]), roman
    return normalized, None


class SubjectResolver:
    """Resolve user expressions against a supplied authoritative catalog."""

    def resolve(self, catalog: List[Dict[str, Any]], expression: str):
        expression_normalized = normalize_subject(expression)
        expression_family, expression_level = subject_parts(expression)
        unique = {}
        for candidate in catalog:
            code = candidate.get("codigo")
            name = candidate.get("nombre")
            if code is not None and name:
                unique[code] = {"codigo": code, "nombre": name}
        candidates = list(unique.values())

        parsed = [
            (candidate, *subject_parts(candidate["nombre"]))
            for candidate in candidates
        ]

        if expression_level is not None:
            numbered = [
                candidate
                for candidate, family, level in parsed
                if family == expression_family and level == expression_level
            ]
            if len(numbered) == 1:
                return "resolved", numbered[0]
            if len(numbered) > 1:
                return "ambiguous", numbered
            return "not_found", []

        numbered_family = [
            (candidate, level)
            for candidate, family, level in parsed
            if family == expression_family and level is not None
        ]
        if numbered_family:
            first_level = [
                candidate for candidate, level in numbered_family if level == 1
            ]
            if len(first_level) == 1:
                return "resolved", first_level[0]
            if len(first_level) > 1:
                return "ambiguous", first_level
            return "not_found", []

        exact = [
            candidate
            for candidate in candidates
            if normalize_subject(candidate["nombre"]) == expression_normalized
        ]
        if len(exact) == 1:
            return "resolved", exact[0]
        if len(exact) > 1:
            return "ambiguous", exact

        partial = [
            candidate
            for candidate in candidates
            if expression_normalized in normalize_subject(candidate["nombre"])
        ]
        if len(partial) == 1:
            return "resolved", partial[0]
        if len(partial) > 1:
            return "ambiguous", partial
        return "not_found", []
