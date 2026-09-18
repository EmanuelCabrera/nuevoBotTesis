"""Baseline characterization tests for action_consultar_fechas_parciales."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class _Action: pass
class _Tracker:
    def __init__(self, slots): self.slots = slots
    def get_slot(self, name): return self.slots.get(name)
class _Dispatcher:
    def __init__(self): self.messages = []
    def utter_message(self, text=None, **kwargs):
        self.messages.append(text if text is not None else kwargs.get("text"))
class _SlotSet:
    def __init__(self, key, value): self.key, self.value = key, value


def _load_module():
    rasa_sdk = types.ModuleType("rasa_sdk")
    rasa_sdk.Action, rasa_sdk.Tracker = _Action, _Tracker
    executor = types.ModuleType("rasa_sdk.executor"); executor.CollectingDispatcher = _Dispatcher
    events = types.ModuleType("rasa_sdk.events"); events.SlotSet = _SlotSet
    dotenv = types.ModuleType("dotenv"); dotenv.load_dotenv = lambda: None
    supabase = types.ModuleType("supabase")
    supabase.Client = object; supabase.create_client = lambda *_: object()
    httpx = types.ModuleType("httpx")
    modules = {"rasa_sdk": rasa_sdk, "rasa_sdk.executor": executor,
               "rasa_sdk.events": events, "dotenv": dotenv,
               "supabase": supabase, "httpx": httpx}
    path = Path(__file__).parents[1] / "actions" / "actions.py"
    spec = importlib.util.spec_from_file_location("partial_actions_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules): spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, backend, table):
        self.backend, self.table, self.filters = backend, table, []
    def select(self, fields): self.backend.calls.append((self.table, "select", fields)); return self
    def ilike(self, column, value):
        self.backend.calls.append((self.table, "ilike", column, value))
        self.filters.append(("ilike", column, value)); return self
    def eq(self, column, value):
        self.backend.calls.append((self.table, "eq", column, value))
        self.filters.append(("eq", column, value)); return self
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
        self.rows, self.errors, self.calls = rows or {}, errors or {}, []
        self.rows.setdefault("Materia", [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "RED2", "nombre": "Redes de Computadoras II"},
        ])
        self.rows.setdefault("Parciales", [])
    def table(self, name): self.calls.append((name, "table")); return _Query(self, name)


ACTION_MODULE = _load_module()


def _event_dict(events): return {event.key: event.value for event in events}


class PartialExamDatesActionBaselineTests(unittest.TestCase):
    def setUp(self):
        self.action = ACTION_MODULE.ActionConsultarFechasParciales()
        self.dispatcher = _Dispatcher()

    def run_action(self, slots, backend):
        ACTION_MODULE.supabase = backend
        ACTION_MODULE.subject_catalog = ACTION_MODULE.SubjectCatalogRepository(
            lambda: ACTION_MODULE.supabase,
            ttl_seconds=600,
        )
        return self.action.run(self.dispatcher, _Tracker(slots), {})

    def slots(self, materia="Física I", matricula="66001", authenticated=True):
        return {"is_authenticated": authenticated, "matricula": matricula,
                "materia": materia, "flujo_actual": "consultar_fechas_parciales"}

    def test_authentication_is_required(self):
        backend = _Backend()
        self.run_action(self.slots(authenticated=False), backend)
        self.assertIn("Necesitas estar autenticado", self.dispatcher.messages[0])
        self.assertFalse(backend.calls)

    def test_missing_matricula_preserves_flow(self):
        events = self.run_action(self.slots(matricula=None), _Backend())
        self.assertIn("número de matrícula", self.dispatcher.messages[0])
        self.assertEqual(_event_dict(events), {"flujo_actual": "consultar_fechas_parciales"})

    def test_missing_materia_preserves_flow(self):
        events = self.run_action(self.slots(materia=None), _Backend())
        self.assertIn("materia especificada", self.dispatcher.messages[0])
        self.assertEqual(_event_dict(events), {"flujo_actual": "consultar_fechas_parciales"})

    def test_exact_subject_queries_partial_code_and_returns_date(self):
        backend = _Backend({"Parciales": [{"id": 1, "fecha_parcial": "2025-08-19", "materia_codigo": "FIS1"}]})
        self.run_action(self.slots(), backend)
        self.assertIn(("Parciales", "eq", "materia_codigo", "FIS1"), backend.calls)
        self.assertIn("2025-08-19", "\n".join(self.dispatcher.messages))

    def test_multiple_dates_are_returned_in_date_order(self):
        backend = _Backend({"Parciales": [
            {"id": 2, "fecha_parcial": "2025-09-30", "materia_codigo": "FIS1"},
            {"id": 1, "fecha_parcial": "2025-08-19", "materia_codigo": "FIS1"},
        ]})
        self.run_action(self.slots(), backend)
        output = "\n".join(self.dispatcher.messages)
        self.assertLess(output.index("2025-08-19"), output.index("2025-09-30"))

    def test_valid_subject_without_dates_is_distinct(self):
        events = self.run_action(self.slots(), _Backend())
        self.assertIn("No se encontraron fechas", self.dispatcher.messages[0])
        self.assertNotIn("No se encontró la materia", self.dispatcher.messages[0])
        self.assertEqual(_event_dict(events), {"flujo_actual": None, "materia": None})

    def test_invalid_subject_does_not_query_partials(self):
        backend = _Backend()
        self.run_action(self.slots(materia="Materia inexistente"), backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])
        self.assertFalse(any(call[:2] == ("Parciales", "table") for call in backend.calls))

    def test_numbered_variant_should_use_canonical_subject(self):
        backend = _Backend({"Parciales": [{"fecha_parcial": "2025-08-19", "materia_codigo": "FIS2"}]})
        self.run_action(self.slots(materia="fisica 2"), backend)
        self.assertIn(("Parciales", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_roman_numbered_variant_uses_canonical_subject(self):
        backend = _Backend({"Parciales": [{"fecha_parcial": "2025-08-19", "materia_codigo": "FIS2"}]})
        self.run_action(self.slots(materia="fisica ii"), backend)
        self.assertIn(("Parciales", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_unnumbered_family_defaults_to_level_one(self):
        backend = _Backend({"Parciales": [{"fecha_parcial": "2025-08-19", "materia_codigo": "FIS1"}]})
        self.run_action(self.slots(materia="fisica"), backend)
        self.assertIn(("Parciales", "eq", "materia_codigo", "FIS1"), backend.calls)

    def test_unknown_numbered_level_is_not_invented(self):
        backend = _Backend()
        events = self.run_action(self.slots(materia="fisica 4"), backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])
        self.assertEqual(_event_dict(events), {"materia": None, "flujo_actual": "consultar_fechas_parciales"})

    def test_ambiguous_subject_should_not_select_first_match(self):
        backend = _Backend({"Materia": [
            {"codigo": "FISA", "nombre": "Física Aplicada"},
            {"codigo": "FISE", "nombre": "Física Experimental"},
        ]})
        self.run_action(self.slots(materia="Física"), backend)
        self.assertFalse(any(call[:2] == ("Parciales", "table") for call in backend.calls))
        self.assertTrue(any("Física Aplicada" in message and "Física Experimental" in message for message in self.dispatcher.messages))

    def test_ambiguous_subject_clears_unresolved_value_and_preserves_flow(self):
        backend = _Backend({"Materia": [
            {"codigo": "FISA", "nombre": "Física Aplicada"},
            {"codigo": "FISE", "nombre": "Física Experimental"},
        ]})
        events = self.run_action(self.slots(materia="Física"), backend)
        self.assertEqual(_event_dict(events), {"materia": None, "flujo_actual": "consultar_fechas_parciales"})

    def test_backend_catalog_error_is_controlled(self):
        backend = _Backend(errors={"Materia": RuntimeError("catalog unavailable")})
        self.run_action(self.slots(), backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])

    def test_backend_partial_error_is_controlled(self):
        backend = _Backend(errors={"Parciales": RuntimeError("backend unavailable")})
        self.run_action(self.slots(), backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])

    def test_success_clears_subject_and_flow(self):
        backend = _Backend({"Parciales": [{"fecha_parcial": "2025-08-19", "materia_codigo": "FIS1"}]})
        events = self.run_action(self.slots(), backend)
        self.assertEqual(_event_dict(events), {"flujo_actual": None, "materia": None})


if __name__ == "__main__": unittest.main()
