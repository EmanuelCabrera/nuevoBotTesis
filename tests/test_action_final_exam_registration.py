"""Action tests for the 006 final-exam registration contract.

The tests use a small Supabase-like fake to verify canonical subject
resolution, deterministic table selection, duplicate handling, persistence,
and retry/state behavior without touching live data.
"""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class _Action:
    pass


class _FormValidationAction:
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
        self.key, self.value = key, value


def _load_module():
    rasa_sdk = types.ModuleType("rasa_sdk")
    rasa_sdk.Action = _Action
    rasa_sdk.Tracker = _Tracker
    rasa_sdk.FormValidationAction = _FormValidationAction
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
    path = Path(__file__).parents[1] / "actions" / "actionsMesaExamen.py"
    spec = importlib.util.spec_from_file_location("registration_actions_under_test", path)
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
        self.filters = []
        self.operation = "select"
        self.payload = None
        self.selected = "*"

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

    def order(self, *args, **kwargs):
        self.backend.calls.append((self.table, "order", args, kwargs))
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = payload
        self.backend.calls.append((self.table, "insert", payload))
        return self

    def delete(self):
        self.operation = "delete"
        self.backend.calls.append((self.table, "delete"))
        return self

    def execute(self):
        if self.table in self.backend.errors:
            raise self.backend.errors[self.table]

        if self.operation == "insert":
            self.backend.inserted.append((self.table, self.payload))
            return _Response([self.payload])

        rows = [dict(row) for row in self.backend.rows.get(self.table, [])]
        for kind, column, value in self.filters:
            if kind == "ilike":
                needle = value.strip("%").casefold()
                rows = [row for row in rows if needle in str(row.get(column, "")).casefold()]
            else:
                rows = [row for row in rows if row.get(column) == value]

        if self.operation == "delete":
            deleted = rows
            self.backend.rows[self.table] = [row for row in self.backend.rows.get(self.table, []) if row not in deleted]
            return _Response(deleted)

        if self.table == "MesaExamen" and "Materia(" in self.selected:
            catalog = {row["codigo"]: row for row in self.backend.rows.get("Materia", [])}
            for row in rows:
                subject = catalog.get(row.get("materia_codigo"))
                if subject:
                    row["Materia"] = {"nombre": subject.get("nombre")}
        return _Response(rows)


class _Backend:
    def __init__(self, rows=None, errors=None):
        self.rows = {table: list(values) for table, values in (rows or {}).items()}
        self.errors = errors or {}
        self.calls = []
        self.inserted = []
        self.rows.setdefault(
            "Materia",
            [
                {"codigo": "FIS1", "nombre": "Física I"},
                {"codigo": "FIS2", "nombre": "Física II"},
                {"codigo": "ALG", "nombre": "Álgebra"},
            ],
        )
        self.rows.setdefault("MesaExamen", [])
        self.rows.setdefault("Inscripcion", [])

    def table(self, name):
        self.calls.append((name, "table"))
        return _Query(self, name)


ACTION_MODULE = _load_module()


def _events(events):
    return {(event.key, event.value) for event in events}


class FinalExamRegistrationActionBaselineTests(unittest.TestCase):
    def setUp(self):
        self.dispatcher = _Dispatcher()

    def run_action(self, action, slots, backend):
        ACTION_MODULE.supabase = backend
        ACTION_MODULE.subject_catalog = ACTION_MODULE.SubjectCatalogRepository(
            lambda: ACTION_MODULE.supabase,
            ttl_seconds=600,
        )
        return action.run(self.dispatcher, _Tracker(slots), {})

    def configure_backend(self, backend):
        ACTION_MODULE.supabase = backend
        ACTION_MODULE.subject_catalog = ACTION_MODULE.SubjectCatalogRepository(
            lambda: ACTION_MODULE.supabase,
            ttl_seconds=600,
        )

    def offer(self, slots, backend):
        self.configure_backend(backend)
        return ACTION_MODULE.ValidateInscripcionMesaForm().validate_materia(
            slots.get("materia"), self.dispatcher, _Tracker(slots), {}
        )

    def validate_matricula(self, slot_value, slots, backend):
        self.configure_backend(backend)
        return ACTION_MODULE.ValidateInscripcionMesaForm().validate_matricula(
            slot_value, self.dispatcher, _Tracker(slots), {}
        )

    def register(self, slots, backend):
        return self.run_action(ACTION_MODULE.ActionInscripcionMesaExamen(), slots, backend)

    def test_offer_requires_authentication(self):
        backend = _Backend()
        result = self.validate_matricula(
            "66001", {"is_authenticated": False}, backend
        )
        self.assertIn("Necesitas estar autenticado", self.dispatcher.messages[0])
        self.assertEqual({"matricula": None}, result)
        self.assertFalse(backend.calls)

    def test_offer_requires_matricula_and_preserves_flow(self):
        backend = _Backend()
        result = self.validate_matricula(None, {"is_authenticated": True}, backend)
        self.assertIn("número de matrícula", self.dispatcher.messages[0])
        self.assertEqual({"matricula": None}, result)

    def test_offer_requires_subject_and_preserves_flow(self):
        backend = _Backend()
        result = self.offer(
            {"is_authenticated": True, "matricula": "66001", "materia": None},
            backend,
        )
        self.assertIn("materia", self.dispatcher.messages[0].lower())
        self.assertEqual({"materia": None}, result)

    def test_offer_lists_one_available_table(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]})
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "Física I"}, backend)
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("M1", output)
        self.assertIn("2025-08-10", output)

    def test_offer_lists_all_available_tables(self):
        backend = _Backend({"MesaExamen": [
            {"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"},
            {"codigo": "M2", "fecha": "2025-08-25", "materia_codigo": "FIS1"},
        ]})
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "Física I"}, backend)
        output = "\n".join(self.dispatcher.messages)
        self.assertIn("M1", output)
        self.assertIn("M2", output)

    def test_offer_no_tables_is_distinct(self):
        backend = _Backend()
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "Física I"}, backend)
        self.assertIn("No se encontraron mesas", self.dispatcher.messages[0])

    def test_offer_invalid_subject_is_reported(self):
        backend = _Backend()
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "Materia inexistente"}, backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])

    def test_spec_numbered_subject_uses_canonical_code(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M2", "fecha": "2025-08-25", "materia_codigo": "FIS2"}]})
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "fisica 2"}, backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_roman_numbered_subject_uses_canonical_code(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M2", "fecha": "2025-08-25", "materia_codigo": "FIS2"}]})
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "FISICA II"}, backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS2"), backend.calls)

    def test_case_and_accent_variation_uses_canonical_code(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-25", "materia_codigo": "FIS1"}]})
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "FISICA I"}, backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS1"), backend.calls)

    def test_unnumbered_family_defaults_to_level_one(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-25", "materia_codigo": "FIS1"}]})
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "fisica"}, backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS1"), backend.calls)

    def test_unknown_numbered_level_is_not_found(self):
        backend = _Backend()
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "fisica 9"}, backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])
        self.assertFalse(any(call[:2] == ("MesaExamen", "table") for call in backend.calls))

    def test_spec_ambiguous_subject_does_not_select_first(self):
        backend = _Backend({
            "Materia": [
                {"codigo": "FISA", "nombre": "Física Aplicada"},
                {"codigo": "FISE", "nombre": "Física Experimental"},
            ],
            "MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FISA"}],
        })
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "Física"}, backend)
        self.assertFalse(any(call[:2] == ("MesaExamen", "table") for call in backend.calls))
        self.assertTrue(any("especific" in message.lower() for message in self.dispatcher.messages))

    def test_offer_backend_failure_is_controlled(self):
        backend = _Backend(errors={"Materia": RuntimeError("catalog unavailable")})
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "Física I"}, backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])

    def test_offer_mesa_backend_failure_is_controlled(self):
        backend = _Backend(
            {"Materia": [{"codigo": "FIS1", "nombre": "Física I"}]},
            errors={"MesaExamen": RuntimeError("mesa unavailable")},
        )
        self.offer({"is_authenticated": True, "matricula": "66001", "materia": "fisica"}, backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])

    def test_register_requires_authentication(self):
        backend = _Backend()
        self.register({"is_authenticated": False, "matricula": "66001", "codigo_mesa_examen": "M1"}, backend)
        self.assertIn("Necesitas estar autenticado", self.dispatcher.messages[0])

    def test_register_requires_matricula(self):
        backend = _Backend()
        self.register({"is_authenticated": True, "codigo_mesa_examen": "M1"}, backend)
        self.assertIn("número de matrícula", self.dispatcher.messages[0])

    def test_register_rejects_unknown_table_code(self):
        backend = _Backend()
        self.register({"is_authenticated": True, "matricula": "66001", "codigo_mesa_examen": "UNKNOWN"}, backend)
        self.assertIn("No se encontró una mesa", self.dispatcher.messages[0])

    def test_register_rejects_mesa_from_another_subject(self):
        backend = _Backend({
            "MesaExamen": [{"codigo": "M2", "fecha": "2025-08-25", "materia_codigo": "FIS2"}],
        })
        self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "materia": "Física I",
            "codigo_mesa_examen": "M2",
        }, backend)
        self.assertIn("no corresponde a la materia", self.dispatcher.messages[0].lower())
        self.assertFalse(backend.inserted)

    def test_register_invalid_subject_does_not_query_selected_mesa(self):
        backend = _Backend({
            "MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}],
        })
        self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "materia": "Materia inexistente",
            "codigo_mesa_examen": "M1",
        }, backend)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])
        self.assertFalse(any(call[:2] == ("MesaExamen", "table") for call in backend.calls))

    def test_register_inserts_selected_table_and_clears_state(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]})
        events = self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "materia": "Física I",
            "codigo_mesa_examen": "M1",
        }, backend)
        self.assertEqual(backend.inserted[0][1]["estudiante"], "66001")
        self.assertEqual(backend.inserted[0][1]["codigo_mesa"], "M1")
        self.assertIn(("flujo_actual", None), _events(events))
        self.assertIn(("codigo_mesa_examen", None), _events(events))

    def test_register_duplicate_does_not_insert(self):
        backend = _Backend({
            "MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}],
            "Inscripcion": [{"estudiante": "66001", "codigo_mesa": "M1", "baja": False}],
        })
        events = self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "codigo_mesa_examen": "M1",
        }, backend)
        self.assertFalse(backend.inserted)
        self.assertIn("Ya estás inscrito", self.dispatcher.messages[0])
        self.assertIn(("flujo_actual", None), _events(events))

    def test_register_cancelled_previous_registration_keeps_current_duplicate_semantics(self):
        backend = _Backend({
            "MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}],
            "Inscripcion": [{"estudiante": "66001", "codigo_mesa": "M1", "baja": True}],
        })
        self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "codigo_mesa_examen": "M1",
        }, backend)
        self.assertFalse(backend.inserted)
        self.assertIn("Ya estás inscrito", self.dispatcher.messages[0])

    def test_register_by_date_resolves_table_for_subject(self):
        backend = _Backend({"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]})
        self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "materia": "Física I",
            "fecha_mesa": "2025-08-10",
        }, backend)
        self.assertIn(("MesaExamen", "eq", "materia_codigo", "FIS1"), backend.calls)
        self.assertIn(("MesaExamen", "eq", "fecha", "2025-08-10"), backend.calls)

    def test_register_backend_failure_is_controlled(self):
        backend = _Backend(
            {"MesaExamen": [{"codigo": "M1", "fecha": "2025-08-10", "materia_codigo": "FIS1"}]},
            errors={"Inscripcion": RuntimeError("insert unavailable")},
        )
        self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "codigo_mesa_examen": "M1",
        }, backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])

    def test_register_mesa_lookup_failure_is_controlled(self):
        backend = _Backend(errors={"MesaExamen": RuntimeError("lookup unavailable")})
        self.register({
            "is_authenticated": True,
            "matricula": "66001",
            "codigo_mesa_examen": "M1",
        }, backend)
        self.assertIn("Hubo un error", self.dispatcher.messages[0])


if __name__ == "__main__":
    unittest.main()
