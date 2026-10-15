"""Action tests for the 007 final-exam registration cancellation contract."""

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
    def utter_message(self, text=None, **kwargs): self.messages.append(text or kwargs.get("text"))
class _SlotSet:
    def __init__(self, key, value): self.key, self.value = key, value


class _Response:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, backend, table):
        self.backend, self.table = backend, table
        self.filters, self.operation, self.selected = [], "select", "*"

    def select(self, fields):
        self.selected = fields
        self.backend.calls.append((self.table, "select", fields))
        return self

    def ilike(self, column, value):
        self.backend.calls.append((self.table, "ilike", column, value))
        self.filters.append(("ilike", column, value))
        return self

    def eq(self, column, value):
        self.backend.calls.append((self.table, "eq", column, value))
        self.filters.append(("eq", column, value))
        return self

    def delete(self):
        self.operation = "delete"
        self.backend.calls.append((self.table, "delete"))
        return self

    def execute(self):
        error = self.backend.errors.get((self.table, self.operation))
        if error is None:
            error = self.backend.errors.get(self.table)
        if error is not None:
            raise error
        rows = self.backend.rows.setdefault(self.table, [])
        matched = list(rows)
        for kind, column, value in self.filters:
            if kind == "eq":
                matched = [row for row in matched if str(row.get(column)) == str(value)]
            else:
                needle = str(value).strip("%").casefold()
                matched = [row for row in matched if needle in str(row.get(column, "")).casefold()]
        if self.operation == "delete":
            for row in matched:
                rows.remove(row)
        return _Response(matched)


class _Backend:
    def __init__(self, rows=None, errors=None):
        self.rows = {key: list(value) for key, value in (rows or {}).items()}
        self.errors = errors or {}
        self.calls = []
    def table(self, name): return _Query(self, name)


def _load_module():
    rasa_sdk = types.ModuleType("rasa_sdk")
    rasa_sdk.Action = _Action
    rasa_sdk.Tracker = _Tracker
    rasa_sdk.FormValidationAction = _Action
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
        "rasa_sdk": rasa_sdk, "rasa_sdk.executor": executor,
        "rasa_sdk.events": events, "dotenv": dotenv,
        "supabase": supabase, "httpx": httpx,
    }
    path = Path(__file__).parents[1] / "actions" / "actionsMesaExamen.py"
    spec = importlib.util.spec_from_file_location("cancellation_actions", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


def _events(events):
    return {(event.key, event.value) for event in events}


class FinalExamCancellationActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.action_module = _load_module()

    def setUp(self):
        self.action = self.action_module.ActionCancelarInscripcionMesa()

    def run_action(self, slots, backend):
        self.action_module.supabase = backend
        self.action_module.subject_catalog = self.action_module.SubjectCatalogRepository(
            lambda: self.action_module.supabase,
            ttl_seconds=600,
        )
        dispatcher = _Dispatcher()
        effective_slots = {"is_authenticated": True, **slots}
        events = self.action.run(dispatcher, _Tracker(effective_slots), {})
        return dispatcher, events

    def backend(self, materia_rows=None, mesas=None, registrations=None, errors=None):
        return _Backend({
            "Materia": materia_rows or [{"codigo": "FIS1", "nombre": "Física I"}],
            "MesaExamen": ([{"codigo": "M1", "materia_codigo": "FIS1"}] if mesas is None else mesas),
            "Inscripcion": registrations or [],
        }, errors)

    def test_requires_authentication(self):
        b = self.backend()
        dispatcher, events = self.run_action({
            "is_authenticated": False,
            "matricula": "66001",
            "materia": "Física I",
        }, b)
        self.assertIn("autenticado", dispatcher.messages[0])
        self.assertEqual(events, [])
        self.assertEqual(b.calls, [])

    def test_requires_matricula(self):
        b = self.backend()
        dispatcher, events = self.run_action({"materia": "fisica"}, b)
        self.assertIn("matrícula", dispatcher.messages[0])
        self.assertEqual(b.calls, [])
        self.assertIn(("flujo_actual", "cancelar_inscripcion_mesa_examen"), _events(events))

    def test_requires_materia(self):
        b = self.backend()
        dispatcher, events = self.run_action({"matricula": "66001"}, b)
        self.assertIn("materia", dispatcher.messages[0])
        self.assertEqual(b.calls, [])
        self.assertIn(("flujo_actual", "cancelar_inscripcion_mesa_examen"), _events(events))

    def test_active_registration_is_deleted(self):
        b = self.backend(registrations=[{"id": 1, "estudiante": "66001", "codigo_mesa": "M1", "baja": False}])
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "Física"}, b)
        self.assertTrue(any(call[:2] == ("Inscripcion", "delete") for call in b.calls))
        self.assertTrue(any("cancelada exitosamente" in message for message in dispatcher.messages))
        self.assertEqual(b.rows["Inscripcion"], [])
        self.assertIn(("materia", None), _events(events))
        self.assertIn(("flujo_actual", None), _events(events))

    def test_no_matching_registration_is_reported(self):
        b = self.backend()
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "Física"}, b)
        self.assertTrue(any("No se encontró una inscripción activa" in message for message in dispatcher.messages))
        self.assertIn(("materia", None), _events(events))
        self.assertIn(("flujo_actual", None), _events(events))

    def test_baja_true_row_is_currently_deleted_too(self):
        b = self.backend(registrations=[{"id": 1, "estudiante": "66001", "codigo_mesa": "M1", "baja": True}])
        self.run_action({"matricula": "66001", "materia": "Física"}, b)
        self.assertEqual(b.rows["Inscripcion"], [])

    def test_multiple_matching_registrations_are_all_deleted(self):
        b = self.backend(registrations=[
            {"id": 1, "estudiante": "66001", "codigo_mesa": "M1", "baja": False},
            {"id": 2, "estudiante": "66001", "codigo_mesa": "M2", "baja": False},
        ], mesas=[{"codigo": "M1", "materia_codigo": "FIS1"}, {"codigo": "M2", "materia_codigo": "FIS1"}])
        dispatcher, _ = self.run_action({"matricula": "66001", "materia": "Física"}, b)
        self.assertEqual(len(b.rows["Inscripcion"]), 0)
        self.assertTrue(any("2 inscripciones" in message for message in dispatcher.messages))

    def test_invalid_subject_does_not_query_mesas(self):
        b = self.backend(materia_rows=[])
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "desconocida"}, b)
        self.assertTrue(any("No se encontró la materia" in message for message in dispatcher.messages))
        self.assertFalse(any(call[0] == "MesaExamen" for call in b.calls))
        self.assertIn(("materia", None), _events(events))
        self.assertIn(("flujo_actual", "cancelar_inscripcion_mesa_examen"), _events(events))

    def test_valid_subject_with_no_exam_tables_is_distinct(self):
        b = self.backend(mesas=[])
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "Física"}, b)
        self.assertTrue(any("No se encontraron mesas" in message for message in dispatcher.messages))
        self.assertIn(("flujo_actual", None), _events(events))

    def test_mesa_backend_failure_is_controlled(self):
        b = self.backend(errors={"MesaExamen": RuntimeError("mesa unavailable")})
        dispatcher, _ = self.run_action({"matricula": "66001", "materia": "Física"}, b)
        self.assertTrue(any("error" in message.lower() for message in dispatcher.messages))

    def test_numbered_subject_uses_canonical_code(self):
        b = self.backend(
            materia_rows=[{"codigo": "FIS2", "nombre": "Física II"}],
            mesas=[{"codigo": "M2", "materia_codigo": "FIS2"}],
        )
        dispatcher, _ = self.run_action({"matricula": "66001", "materia": "fisica 2"}, b)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS2"), b.calls)
        self.assertFalse(any("No se encontró la materia" in message for message in dispatcher.messages))

    def test_roman_numbered_subject_uses_canonical_code(self):
        b = self.backend(
            materia_rows=[{"codigo": "FIS2", "nombre": "Física II"}],
            mesas=[{"codigo": "M2", "materia_codigo": "FIS2"}],
        )
        self.run_action({"matricula": "66001", "materia": "FISICA II"}, b)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS2"), b.calls)

    def test_case_and_accent_variation_uses_canonical_code(self):
        b = self.backend(
            materia_rows=[{"codigo": "ALG", "nombre": "Álgebra"}],
            mesas=[{"codigo": "M3", "materia_codigo": "ALG"}],
        )
        self.run_action({"matricula": "66001", "materia": "ALGEBRA"}, b)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "ALG"), b.calls)

    def test_unknown_numbered_level_does_not_query_mesas(self):
        b = self.backend(materia_rows=[
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
        ])
        dispatcher, _ = self.run_action({"matricula": "66001", "materia": "fisica 9"}, b)
        self.assertIn("No se encontró la materia", dispatcher.messages[0])
        self.assertFalse(any(call[0] == "MesaExamen" for call in b.calls))

    def test_ambiguous_subject_requests_clarification(self):
        b = self.backend(materia_rows=[
            {"codigo": "FISA", "nombre": "Física Aplicada"},
            {"codigo": "FISE", "nombre": "Física Experimental"},
        ])
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "Física"}, b)
        self.assertFalse(any(call[0] == "MesaExamen" for call in b.calls))
        self.assertTrue(any("varias materias" in message for message in dispatcher.messages))
        self.assertIn(("materia", None), _events(events))
        self.assertIn(("flujo_actual", "cancelar_inscripcion_mesa_examen"), _events(events))

    def test_backend_failure_is_controlled(self):
        b = self.backend(errors={"Materia": RuntimeError("backend unavailable")})
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "fisica"}, b)
        self.assertTrue(any("error" in message.lower() for message in dispatcher.messages))
        self.assertIn(("flujo_actual", "cancelar_inscripcion_mesa_examen"), _events(events))

    def test_registration_backend_failure_is_controlled(self):
        b = self.backend(errors={"Inscripcion": RuntimeError("registration unavailable")})
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "fisica"}, b)
        self.assertTrue(any("error" in message.lower() for message in dispatcher.messages))
        self.assertIn(("flujo_actual", "cancelar_inscripcion_mesa_examen"), _events(events))

    def test_delete_backend_failure_is_controlled(self):
        b = self.backend(
            registrations=[
                {"id": 1, "estudiante": "66001", "codigo_mesa": "M1", "baja": False}
            ],
            errors={("Inscripcion", "delete"): RuntimeError("delete unavailable")},
        )
        dispatcher, events = self.run_action({"matricula": "66001", "materia": "fisica"}, b)
        self.assertTrue(any("error" in message.lower() for message in dispatcher.messages))
        self.assertEqual(len(b.rows["Inscripcion"]), 1)
        self.assertIn(("flujo_actual", "cancelar_inscripcion_mesa_examen"), _events(events))


if __name__ == "__main__":
    unittest.main()
