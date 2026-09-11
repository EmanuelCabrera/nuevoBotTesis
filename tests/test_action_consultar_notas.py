"""Characterization tests for the current grades action."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class _Action:
    pass


class _Tracker:
    def __init__(self, slots):
        self.slots = slots

    def get_slot(self, name):
        return self.slots.get(name)


class _Dispatcher:
    def __init__(self):
        self.messages = []

    def utter_message(self, text=None, **kwargs):
        self.messages.append(text if text is not None else kwargs.get("text"))


class _SlotSet:
    def __init__(self, key, value):
        self.key = key
        self.value = value


def _load_module():
    rasa_sdk = types.ModuleType("rasa_sdk")
    rasa_sdk.Action = _Action
    rasa_sdk.Tracker = _Tracker
    executor = types.ModuleType("rasa_sdk.executor")
    executor.CollectingDispatcher = _Dispatcher
    events = types.ModuleType("rasa_sdk.events")
    events.SlotSet = _SlotSet
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    supabase = types.ModuleType("supabase")
    supabase.Client = object
    supabase.create_client = lambda _url, _key: object()
    httpx = types.ModuleType("httpx")
    modules = {
        "rasa_sdk": rasa_sdk,
        "rasa_sdk.executor": executor,
        "rasa_sdk.events": events,
        "dotenv": dotenv,
        "supabase": supabase,
        "httpx": httpx,
    }
    path = Path(__file__).parents[1] / "actions" / "actionsMaterias.py"
    spec = importlib.util.spec_from_file_location("grades_actions_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, backend, table):
        self.backend = backend
        self.table = table

    def select(self, fields):
        self.backend.calls.append((self.table, "select", fields))
        return self

    def eq(self, column, value):
        self.backend.calls.append((self.table, "eq", column, value))
        return self

    def execute(self):
        if self.table in self.backend.errors:
            raise self.backend.errors[self.table]
        return _Response(self.backend.rows.get(self.table, []))


class _Backend:
    def __init__(self, rows=None, errors=None, catalog=None):
        self.rows = rows or {}
        self.rows.setdefault("Materia", catalog or [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "FIS3", "nombre": "Física III"},
        ])
        self.errors = errors or {}
        self.calls = []

    def table(self, table):
        self.calls.append((table, "table"))
        return _Query(self, table)


ACTION_MODULE = _load_module()


def _event_dict(events):
    return {event.key: event.value for event in events}


class GradesActionCharacterizationTests(unittest.TestCase):
    def setUp(self):
        self.action = ACTION_MODULE.ActionConsultarNotas()
        self.dispatcher = _Dispatcher()

    def run_action(self, slots, backend):
        ACTION_MODULE.supabase = backend
        return self.action.run(self.dispatcher, _Tracker(slots), {})

    def test_successful_lookup_filters_student_and_returns_supported_fields(self):
        backend = _Backend({"Notas": [{
            "nota": 8,
            "descripcion": "Parcial 1",
            "created_at": "2025-07-14T23:18:07+00:00",
            "Materia": {"nombre": "Física I", "codigo": "FIS1"},
        }]})
        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física I"},
            backend,
        )
        self.assertIn(("Notas", "eq", "estudiante_id", 66001), backend.calls)
        self.assertIn("8/10", "\n".join(self.dispatcher.messages))
        self.assertIn("Parcial 1", "\n".join(self.dispatcher.messages))
        self.assertIn("14/07/2025", "\n".join(self.dispatcher.messages))
        self.assertEqual(_event_dict(events), {"flujo_actual": None, "materia": None})

    def test_multiple_grade_records_are_returned_individually(self):
        backend = _Backend({"Notas": [
            {"nota": 4, "descripcion": "Parcial 1", "created_at": "2025-04-01T00:00:00+00:00", "Materia": {"nombre": "Física I"}},
            {"nota": 9, "descripcion": "Parcial 2", "created_at": "2025-05-01T00:00:00+00:00", "Materia": {"nombre": "Física I"}},
        ]})
        self.run_action({"is_authenticated": True, "matricula": "66001", "materia": "Física I"}, backend)
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("Parcial 1", output)
        self.assertIn("Parcial 2", output)
        self.assertIn("Total de notas encontradas: 2", output)

    def test_valid_subject_with_no_grades(self):
        backend = _Backend({"Notas": []})
        self.run_action({"is_authenticated": True, "matricula": "66001", "materia": "fisica"}, backend)
        self.assertIn("No se encontraron notas", self.dispatcher.messages[0])

    def test_invalid_subject_when_student_has_other_grades(self):
        backend = _Backend({"Notas": [{"nota": 7, "Materia": {"nombre": "Física I"}}]})
        self.run_action({"is_authenticated": True, "matricula": "66001", "materia": "Materia inexistente"}, backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])

    def test_missing_authentication(self):
        backend = _Backend()
        self.run_action({"is_authenticated": False, "matricula": "66001", "materia": "fisica"}, backend)
        self.assertIn("Necesitas estar autenticado", self.dispatcher.messages[0])

    def test_missing_matricula(self):
        backend = _Backend()
        events = self.run_action({"is_authenticated": True, "materia": "fisica"}, backend)
        self.assertIn("No tengo tu número de matrícula", self.dispatcher.messages[0])
        self.assertEqual(_event_dict(events), {"flujo_actual": "consultar_notas"})

    def test_missing_materia(self):
        backend = _Backend()
        events = self.run_action({"is_authenticated": True, "matricula": "66001"}, backend)
        self.assertIn("No tengo la materia especificada", self.dispatcher.messages[0])
        self.assertEqual(_event_dict(events), {"flujo_actual": "consultar_notas"})

    def test_invalid_matricula_format(self):
        backend = _Backend()
        self.run_action({"is_authenticated": True, "matricula": "abc", "materia": "fisica"}, backend)
        self.assertIn("debe ser un número válido", self.dispatcher.messages[0])

    def test_backend_exception_is_controlled(self):
        backend = _Backend(errors={"Notas": RuntimeError("backend unavailable")})
        self.run_action({"is_authenticated": True, "matricula": "66001", "materia": "fisica"}, backend)
        self.assertIn("Hubo un error al consultar tus notas", self.dispatcher.messages[0])

    def test_spec_canonical_numbered_resolution_uses_catalog_identity(self):
        backend = _Backend({"Notas": [{"nota": 8, "Materia": {"nombre": "Física II", "codigo": "FIS2"}}]})
        self.run_action({"is_authenticated": True, "matricula": "66001", "materia": "fisica 2"}, backend)
        # Characterization expectation: the action should constrain by canonical codigo.
        self.assertIn(("Notas", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_spec_ambiguous_subject_must_not_query_arbitrarily(self):
        backend = _Backend(
            {"Notas": [{"nota": 8, "Materia": {"nombre": "Física I", "codigo": "FIS1"}}]},
            catalog=[
                {"codigo": "FIS1A", "nombre": "Física I"},
                {"codigo": "FIS1B", "nombre": "Física I"},
            ],
        )
        self.run_action({"is_authenticated": True, "matricula": "66001", "materia": "fisica"}, backend)
        self.assertFalse(any(call[:2] == ("Notas", "table") for call in backend.calls))

    def test_subject_is_cleared_after_successful_query(self):
        backend = _Backend({"Notas": [{"nota": 8, "Materia": {"nombre": "Física I"}}]})
        events = self.run_action({"is_authenticated": True, "matricula": "66001", "materia": "Física I"}, backend)
        self.assertEqual(_event_dict(events).get("materia"), None)


if __name__ == "__main__":
    unittest.main()
