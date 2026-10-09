"""Contract tests for the course-records action."""

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
        error = self.backend.errors.get(self.table)
        if error is not None:
            raise error
        return _Response(self.backend.rows.get(self.table, []))


class _Backend:
    def __init__(self, rows=None, errors=None):
        self.rows = rows or {}
        self.errors = errors or {}
        self.calls = []

    def table(self, table):
        self.calls.append((table, "table"))
        return _Query(self, table)


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
    supabase.create_client = lambda *_: object()
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
    spec = importlib.util.spec_from_file_location("enrolled_subjects_actions", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


ACTION_MODULE = _load_module()


def _events(events):
    return {event.key: event.value for event in events}


class CourseRecordsActionTests(unittest.TestCase):
    def setUp(self):
        self.action = ACTION_MODULE.ActionConsultarMaterias()
        self.dispatcher = _Dispatcher()

    def run_action(self, slots, backend):
        ACTION_MODULE.supabase = backend
        return self.action.run(self.dispatcher, _Tracker(slots), {})

    def test_action_name(self):
        self.assertEqual(self.action.name(), "action_consultar_materias")

    def test_authentication_is_required_before_querying(self):
        backend = _Backend()
        events = self.run_action(
            {"is_authenticated": False, "matricula": "66001"}, backend
        )
        self.assertIn("autenticado", self.dispatcher.messages[0])
        self.assertEqual(backend.calls, [])
        self.assertEqual(_events(events), {"flujo_actual": None})

    def test_missing_matricula_preserves_legacy_flow_marker(self):
        backend = _Backend()
        events = self.run_action({"is_authenticated": True}, backend)
        self.assertIn("matrícula", self.dispatcher.messages[0])
        self.assertEqual(backend.calls, [])
        self.assertEqual(_events(events), {"flujo_actual": "consultar_materias"})

    def test_one_row_uses_student_filter_and_related_canonical_name(self):
        backend = _Backend({"MateriaCursada": [{
            "fecha_cursada": "2025-03-01",
            "Materia": {"nombre": "Física II"},
        }]})
        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001"}, backend
        )
        self.assertIn(
            ("MateriaCursada", "select", "fecha_cursada, Materia(nombre)"),
            backend.calls,
        )
        self.assertIn(("MateriaCursada", "eq", "estudiante", "66001"), backend.calls)
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("Física II", output)
        self.assertIn("2025-03-01", output)
        self.assertIn("Registros de materias cursadas", output)
        self.assertIn("Total de registros de cursada encontrados: 1", output)
        self.assertEqual(_events(events), {"flujo_actual": None})

    def test_multiple_rows_are_ordered_by_date_then_canonical_name(self):
        backend = _Backend({"MateriaCursada": [
            {"fecha_cursada": "2024-03-01", "Materia": {"nombre": "Redes II"}},
            {"fecha_cursada": "2023-03-01", "Materia": {"nombre": "Física II"}},
            {"fecha_cursada": "2023-03-01", "Materia": {"nombre": "Álgebra I"}},
        ]})
        self.run_action(
            {"is_authenticated": True, "matricula": "66001"}, backend
        )
        output = "\n".join(self.dispatcher.messages)
        self.assertLess(output.index("Física II"), output.index("Álgebra I"))
        self.assertLess(output.index("Álgebra I"), output.index("Redes II"))
        self.assertIn("Total de registros de cursada encontrados: 3", output)

    def test_approval_state_is_not_selected_or_used(self):
        backend = _Backend({"MateriaCursada": [
            {"fecha_cursada": "2022-03-01", "aprobada": True, "Materia": {"nombre": "A"}},
            {"fecha_cursada": "2023-03-01", "aprobada": False, "Materia": {"nombre": "B"}},
            {"fecha_cursada": "2024-03-01", "aprobada": None, "Materia": {"nombre": "C"}},
        ]})
        self.run_action(
            {"is_authenticated": True, "matricula": "66001"}, backend
        )
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("A", output)
        self.assertIn("B", output)
        self.assertIn("C", output)
        self.assertIn("Total de registros de cursada encontrados: 3", output)

    def test_duplicate_rows_are_displayed_and_counted(self):
        duplicate = {
            "fecha_cursada": "2025-03-01",
            "Materia": {"nombre": "Física II"},
        }
        backend = _Backend({"MateriaCursada": [duplicate, dict(duplicate)]})
        self.run_action(
            {"is_authenticated": True, "matricula": "66001"}, backend
        )
        output = "\n".join(self.dispatcher.messages)
        self.assertEqual(output.count("Física II"), 2)
        self.assertIn("Total de registros de cursada encontrados: 2", output)

    def test_no_rows_cannot_distinguish_invalid_student(self):
        backend = _Backend({"MateriaCursada": []})
        events = self.run_action(
            {"is_authenticated": True, "matricula": "99999", "materia": "stale"},
            backend,
        )
        self.assertIn("No se encontraron registros de materias cursadas", self.dispatcher.messages[0])
        self.assertEqual(_events(events), {"flujo_actual": None})

    def test_backend_failure_is_controlled_and_cleans_flow_state(self):
        backend = _Backend(errors={"MateriaCursada": RuntimeError("unavailable")})
        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001"}, backend
        )
        self.assertIn("error", self.dispatcher.messages[0].lower())
        self.assertEqual(_events(events), {"flujo_actual": None})

    def test_subject_catalog_and_resolver_are_not_queried(self):
        backend = _Backend({"MateriaCursada": []})
        self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física"},
            backend,
        )
        self.assertEqual([call for call in backend.calls if call[1] == "table"], [
            ("MateriaCursada", "table")
        ])


if __name__ == "__main__":
    unittest.main()
