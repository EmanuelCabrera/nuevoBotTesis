"""Specification-focused baseline tests for action_consultar_mesas_examen."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class _Action: pass
class _FormValidationAction: pass
class _Tracker:
    def __init__(self, slots): self.slots = slots
    def get_slot(self, name): return self.slots.get(name)
class _Dispatcher:
    def __init__(self): self.messages = []
    def utter_message(self, text=None, **kwargs): self.messages.append(text if text is not None else kwargs.get("text"))
class _SlotSet:
    def __init__(self, key, value): self.key, self.value = key, value


def _load_module():
    rasa_sdk = types.ModuleType("rasa_sdk")
    rasa_sdk.Action, rasa_sdk.Tracker, rasa_sdk.FormValidationAction = _Action, _Tracker, _FormValidationAction
    executor = types.ModuleType("rasa_sdk.executor"); executor.CollectingDispatcher = _Dispatcher
    events = types.ModuleType("rasa_sdk.events"); events.SlotSet = _SlotSet
    dotenv = types.ModuleType("dotenv"); dotenv.load_dotenv = lambda: None
    supabase = types.ModuleType("supabase"); supabase.Client = object; supabase.create_client = lambda *_: object()
    httpx = types.ModuleType("httpx")
    modules = {"rasa_sdk": rasa_sdk, "rasa_sdk.executor": executor, "rasa_sdk.events": events,
               "dotenv": dotenv, "supabase": supabase, "httpx": httpx}
    path = Path(__file__).parents[1] / "actions" / "actionsMesaExamen.py"
    spec = importlib.util.spec_from_file_location("mesa_actions_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules): spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, backend, table): self.backend, self.table, self.filters = backend, table, []
    def select(self, fields): self.backend.calls.append((self.table, "select", fields)); return self
    def ilike(self, column, value): self.backend.calls.append((self.table, "ilike", column, value)); self.filters.append(("ilike", column, value)); return self
    def eq(self, column, value): self.backend.calls.append((self.table, "eq", column, value)); self.filters.append(("eq", column, value)); return self
    def order(self, *args, **kwargs): return self
    def execute(self):
        if self.table in self.backend.errors: raise self.backend.errors[self.table]
        rows = list(self.backend.rows.get(self.table, []))
        for kind, column, value in self.filters:
            if kind == "ilike":
                needle = value.strip("%").casefold()
                rows = [row for row in rows if needle in str(row.get(column, "")).casefold()]
            else:
                rows = [row for row in rows if row.get(column) == value]
        return _Response(rows)


class _Backend:
    def __init__(self, rows=None, errors=None):
        self.rows = rows or {}
        self.errors = errors or {}
        self.calls = []
        self.rows.setdefault("Materia", [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "RED2", "nombre": "Redes de Computadoras II"},
        ])
        self.rows.setdefault("MesaExamen", [])
    def table(self, name): self.calls.append((name, "table")); return _Query(self, name)


ACTION_MODULE = _load_module()


def _events(events): return {(event.key, event.value) for event in events}


class FinalExamDatesActionBaselineTests(unittest.TestCase):
    def setUp(self):
        self.action = ACTION_MODULE.ActionVerMesasExamen()
        self.dispatcher = _Dispatcher()

    def run_action(self, materia, backend, authenticated=True):
        ACTION_MODULE.supabase = backend
        ACTION_MODULE.subject_catalog = ACTION_MODULE.SubjectCatalogRepository(
            lambda: ACTION_MODULE.supabase,
            ttl_seconds=600,
        )
        return self.action.run(
            self.dispatcher,
            _Tracker(
                {
                    "is_authenticated": authenticated,
                    "materia": materia,
                    "flujo_actual": "consultar_fecha_mesas_examen_final",
                }
            ),
            {},
        )

    def test_authentication_is_required(self):
        backend = _Backend()
        self.run_action("Física I", backend, authenticated=False)
        self.assertIn("Necesitas estar autenticado", self.dispatcher.messages[0])
        self.assertFalse(backend.calls)

    def test_exact_valid_subject_queries_canonical_code(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]})
        self.run_action("Física I", backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS1"), backend.calls)

    def test_numbered_variant_resolves_to_canonical_subject(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M2", "fecha": "2025-08-25", "materia_codigo": "FIS2"}]})
        self.run_action("fisica 2", backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_roman_numbered_variant_resolves_to_canonical_subject(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M2", "fecha": "2025-08-25", "materia_codigo": "FIS2"}]})
        self.run_action("fisica ii", backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_accent_and_case_are_normalized(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M2", "fecha": "2025-08-25", "materia_codigo": "FIS2"}]})
        self.run_action("FÍSICA II", backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_invalid_subject_does_not_query_mesas(self):
        backend = _Backend()
        self.run_action("Materia inexistente", backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])
        self.assertFalse(any(call[:2] == ("MesaExamen", "table") for call in backend.calls))

    def test_unknown_numbered_level_is_not_invented(self):
        backend = _Backend()
        self.run_action("fisica 4", backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])
        self.assertFalse(any(call[:2] == ("MesaExamen", "table") for call in backend.calls))

    def test_ambiguous_subject_does_not_select_first_match(self):
        backend = _Backend({"Materia": [
            {"codigo": "FISA", "nombre": "Física Aplicada"},
            {"codigo": "FISE", "nombre": "Física Experimental"},
        ]})
        self.run_action("Física", backend)
        self.assertFalse(any(call[:2] == ("MesaExamen", "table") for call in backend.calls))
        self.assertTrue(any("especific" in message.lower() for message in self.dispatcher.messages))

    def test_ambiguous_subject_preserves_flow_and_clears_unresolved_value(self):
        backend = _Backend({"Materia": [
            {"codigo": "FISA", "nombre": "Física Aplicada"},
            {"codigo": "FISE", "nombre": "Física Experimental"},
        ]})
        events = self.run_action("Física", backend)
        self.assertIn(("flujo_actual", "consultar_fecha_mesas_examen_final"), _events(events))
        self.assertIn(("materia", None), _events(events))

    def test_valid_subject_without_mesas_is_distinct(self):
        backend = _Backend()
        events = self.run_action("Física I", backend)
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("No se encontraron mesas", output)
        self.assertNotIn("No se encontró la materia", output)
        self.assertIn(("materia", None), _events(events))
        self.assertIn(("flujo_actual", None), _events(events))

    def test_one_mesa_returns_code_and_date(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]})
        self.run_action("Física I", backend)
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("M1", output); self.assertIn("2025-08-10", output)

    def test_multiple_mesas_are_all_returned(self):
        backend = _Backend({"MesaExamen": [
            {"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"},
            {"codigo": "M3", "fecha": "2025-08-25", "materia_codigo": "FIS1"},
        ]})
        self.run_action("Física I", backend)
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("M1", output); self.assertIn("M3", output)
        self.assertIn("2025-08-10", output); self.assertIn("2025-08-25", output)

    def test_response_uses_canonical_subject_name(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]})
        self.run_action("Física I", backend)
        self.assertIn("FÍSICA I", "\n".join(self.dispatcher.messages))

    def test_backend_mesas_failure_is_controlled(self):
        backend = _Backend(errors={"MesaExamen": RuntimeError("backend unavailable")})
        self.run_action("Física I", backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])

    def test_backend_catalog_failure_is_controlled(self):
        backend = _Backend(errors={"Materia": RuntimeError("catalog unavailable")})
        self.run_action("Física I", backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])
        self.assertFalse(any(call[:2] == ("MesaExamen", "table") for call in backend.calls))

    def test_success_clears_subject_state(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]})
        events = self.run_action("Física I", backend)
        self.assertIn(("materia", None), _events(events))
        self.assertIn(("flujo_actual", None), _events(events))


if __name__ == "__main__": unittest.main()
