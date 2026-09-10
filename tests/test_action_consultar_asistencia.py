"""Unit characterization tests for action_consultar_asistencia.

The action module initializes its Supabase client at import time. These tests use
small SDK and dependency doubles while importing the module, then replace that
client with an in-memory query fake. No network or real Supabase backend is used.
"""

from __future__ import annotations

import importlib.util
import re
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


class _CollectingDispatcher:
    def __init__(self):
        self.messages = []

    def utter_message(self, text=None, **kwargs):
        self.messages.append(text if text is not None else kwargs.get("text"))


class _SlotSet:
    def __init__(self, key, value):
        self.key = key
        self.value = value


def _load_actions_module():
    rasa_sdk = types.ModuleType("rasa_sdk")
    rasa_sdk.Action = _Action
    rasa_sdk.Tracker = _Tracker

    executor = types.ModuleType("rasa_sdk.executor")
    executor.CollectingDispatcher = _CollectingDispatcher

    events = types.ModuleType("rasa_sdk.events")
    events.SlotSet = _SlotSet

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None

    supabase = types.ModuleType("supabase")
    supabase.Client = object
    supabase.create_client = lambda _url, _key: object()

    httpx = types.ModuleType("httpx")

    dependency_doubles = {
        "rasa_sdk": rasa_sdk,
        "rasa_sdk.executor": executor,
        "rasa_sdk.events": events,
        "dotenv": dotenv,
        "supabase": supabase,
        "httpx": httpx,
    }

    path = Path(__file__).parents[1] / "actions" / "actions.py"
    spec = importlib.util.spec_from_file_location("attendance_actions_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, dependency_doubles):
        spec.loader.exec_module(module)
    return module


ACTION_MODULE = _load_actions_module()


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, backend, table_name):
        self.backend = backend
        self.table_name = table_name

    def select(self, columns):
        self.backend.calls.append((self.table_name, "select", columns))
        return self

    def ilike(self, column, value):
        self.backend.calls.append((self.table_name, "ilike", column, value))
        return self

    def eq(self, column, value):
        self.backend.calls.append((self.table_name, "eq", column, value))
        return self

    def execute(self):
        if self.table_name in self.backend.errors:
            raise self.backend.errors[self.table_name]
        return _Response(self.backend.rows.get(self.table_name, []))


class _FakeSupabase:
    def __init__(self, rows=None, errors=None):
        self.rows = rows or {}
        self.errors = errors or {}
        self.calls = []

    def table(self, table_name):
        self.calls.append((table_name, "table"))
        return _Query(self, table_name)


class _CatalogQuery(_Query):
    """Small catalog double that approximates accent-sensitive SQL ILIKE."""

    def __init__(self, backend, table_name):
        super().__init__(backend, table_name)
        self._subject_pattern = None

    def ilike(self, column, value):
        super().ilike(column, value)
        self._subject_pattern = value.strip("%").casefold()
        return self

    def execute(self):
        if self.table_name in self.backend.errors:
            raise self.backend.errors[self.table_name]
        rows = self.backend.rows.get(self.table_name, [])
        if self.table_name == "Materia" and self._subject_pattern is not None:
            rows = [
                row for row in rows
                if self._subject_pattern in row.get("nombre", "").casefold()
            ]
        return _Response(rows)


class _CatalogSupabase(_FakeSupabase):
    def table(self, table_name):
        self.calls.append((table_name, "table"))
        return _CatalogQuery(self, table_name)


def _events_as_dict(events):
    return {event.key: event.value for event in events}


class ActionConsultarAsistenciaTests(unittest.TestCase):
    def setUp(self):
        self.action = ACTION_MODULE.ActionConsultarAsistencia()
        self.dispatcher = _CollectingDispatcher()

    def run_action(self, slots, backend):
        ACTION_MODULE.supabase = backend
        tracker = _Tracker(slots)
        return self.action.run(self.dispatcher, tracker, {})

    def test_successful_query_filters_by_student_and_subject(self):
        backend = _FakeSupabase(
            rows={
                "Materia": [{"codigo": "FIS1", "nombre": "Física"}],
                "Asistencia": [{"is_present": True}],
            }
        )

        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física"},
            backend,
        )

        self.assertIn(("Materia", "select", "codigo, nombre"), backend.calls)
        self.assertIn(("Asistencia", "eq", "estudiante", "66001"), backend.calls)
        self.assertIn(("Asistencia", "eq", "materia", "FIS1"), backend.calls)
        self.assertTrue(any("Asistencia en FÍSICA" in message for message in self.dispatcher.messages))
        self.assertEqual(
            _events_as_dict(events),
            {"flujo_actual": None, "materia": None},
        )

    def test_present_absent_total_and_percentage_calculation(self):
        backend = _FakeSupabase(
            rows={
                "Materia": [{"codigo": "MAT1", "nombre": "Matemática"}],
                "Asistencia": [
                    {"is_present": True},
                    {"is_present": True},
                    {"is_present": True},
                    {"is_present": False},
                ],
            }
        )

        self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Matemática"},
            backend,
        )

        output = "\n".join(self.dispatcher.messages)
        self.assertIn("Clases asistidas: 3", output)
        self.assertIn("Clases ausentes: 1", output)
        self.assertIn("Total de clases: 4", output)
        self.assertIn("Porcentaje de asistencia: 75.0%", output)

    def test_successful_response_is_consistent_and_reports_requested_subject(self):
        backend = _FakeSupabase(
            rows={
                "Materia": [{"codigo": "FIS1", "nombre": "Física"}],
                "Asistencia": [
                    {"is_present": True},
                    {"is_present": True},
                    {"is_present": False},
                    {"is_present": False},
                    {"is_present": True},
                ],
            }
        )

        self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física"},
            backend,
        )

        output = "\n".join(self.dispatcher.messages)
        attended = int(re.search(r"Clases asistidas: (\d+)", output).group(1))
        absent = int(re.search(r"Clases ausentes: (\d+)", output).group(1))
        total = int(re.search(r"Total de clases: (\d+)", output).group(1))
        percentage = float(
            re.search(r"Porcentaje de asistencia: ([\d.]+)%", output).group(1)
        )

        self.assertIn("Asistencia en FÍSICA", output)
        self.assertEqual(total, attended + absent)
        self.assertAlmostEqual(percentage, attended / total * 100, places=2)
        self.assertIn(("Asistencia", "eq", "materia", "FIS1"), backend.calls)

    def test_no_matching_subject(self):
        backend = _FakeSupabase(rows={"Materia": []})

        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Astrofísica"},
            backend,
        )

        self.assertEqual(len(self.dispatcher.messages), 1)
        self.assertIn("No se encontró la materia 'Astrofísica'", self.dispatcher.messages[0])
        self.assertEqual(_events_as_dict(events), {"flujo_actual": None})
        self.assertNotIn(("Asistencia", "table"), backend.calls)

    def test_no_attendance_records(self):
        backend = _FakeSupabase(
            rows={
                "Materia": [{"codigo": "FIS1", "nombre": "Física"}],
                "Asistencia": [],
            }
        )

        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física"},
            backend,
        )

        self.assertEqual(len(self.dispatcher.messages), 1)
        self.assertIn("No se encontraron registros de asistencia", self.dispatcher.messages[0])
        self.assertEqual(_events_as_dict(events), {"flujo_actual": None})

    def test_missing_required_data(self):
        cases = [
            (
                {"is_authenticated": False, "matricula": "66001", "materia": "Física"},
                "Necesitas estar autenticado",
                {},
            ),
            (
                {"is_authenticated": True, "materia": "Física"},
                "No tengo tu número de matrícula",
                {"flujo_actual": "consultar_asistencia"},
            ),
            (
                {"is_authenticated": True, "matricula": "66001"},
                "No tengo la materia especificada",
                {"flujo_actual": "consultar_asistencia"},
            ),
        ]

        for slots, expected_message, expected_events in cases:
            with self.subTest(slots=slots):
                self.dispatcher = _CollectingDispatcher()
                backend = _FakeSupabase()
                events = self.run_action(slots, backend)
                self.assertIn(expected_message, self.dispatcher.messages[0])
                self.assertEqual(_events_as_dict(events), expected_events)
                self.assertEqual(backend.calls, [])

    def test_backend_error_is_reported_without_events(self):
        backend = _FakeSupabase(errors={"Materia": RuntimeError("backend unavailable")})

        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física"},
            backend,
        )

        self.assertEqual(events, [])
        self.assertEqual(len(self.dispatcher.messages), 1)
        self.assertIn("Hubo un error al consultar tu asistencia", self.dispatcher.messages[0])

    def test_accent_and_case_variants_resolve_to_catalog_canonical_name(self):
        for expression in ("fisica", "FISICA", "Fisica"):
            with self.subTest(expression=expression):
                self.dispatcher = _CollectingDispatcher()
                backend = _CatalogSupabase(
                    rows={
                        "Materia": [{"codigo": "FIS1", "nombre": "Física"}],
                        "Asistencia": [{"is_present": True}],
                    }
                )

                self.run_action(
                    {"is_authenticated": True, "matricula": "66001", "materia": expression},
                    backend,
                )

                output = "\n".join(self.dispatcher.messages)
                self.assertIn("Asistencia en FÍSICA", output)
                self.assertIn(("Asistencia", "eq", "materia", "FIS1"), backend.calls)

    def test_distinct_numbered_subject_is_not_replaced_by_first_partial_match(self):
        backend = _CatalogSupabase(
            rows={
                "Materia": [
                    {"codigo": "FIS1", "nombre": "Física I"},
                    {"codigo": "FIS2", "nombre": "Física II"},
                ],
                "Asistencia": [{"is_present": True}],
            }
        )

        self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física II"},
            backend,
        )

        self.assertIn(("Asistencia", "eq", "materia", "FIS2"), backend.calls)

    def test_ambiguous_subject_requests_clarification_without_querying_attendance(self):
        backend = _CatalogSupabase(
            rows={
                "Materia": [
                    {"codigo": "FISA", "nombre": "Física Aplicada"},
                    {"codigo": "FISE", "nombre": "Física Experimental"},
                ],
                "Asistencia": [{"is_present": True}],
            }
        )

        events = self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física"},
            backend,
        )

        self.assertTrue(any("varias materias" in message.lower() for message in self.dispatcher.messages))
        self.assertEqual(_events_as_dict(events), {"flujo_actual": "consultar_asistencia", "materia": None})
        self.assertNotIn(("Asistencia", "table"), backend.calls)

    def test_clarification_continues_original_attendance_flow(self):
        backend = _CatalogSupabase(
            rows={
                "Materia": [
                    {"codigo": "FISA", "nombre": "Física Aplicada"},
                    {"codigo": "FISE", "nombre": "Física Experimental"},
                ],
                "Asistencia": [{"is_present": True}],
            }
        )

        first_events = self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física"},
            backend,
        )
        self.assertEqual(_events_as_dict(first_events), {"flujo_actual": "consultar_asistencia", "materia": None})
        backend.calls.clear()
        self.dispatcher = _CollectingDispatcher()

        self.run_action(
            {"is_authenticated": True, "matricula": "66001", "materia": "Física Experimental"},
            backend,
        )

        self.assertIn(("Asistencia", "eq", "materia", "FISE"), backend.calls)

    def test_multiword_subject_resolves_exact_canonical_entry(self):
        backend = _CatalogSupabase(
            rows={
                "Materia": [
                    {"codigo": "RC10", "nombre": "Redes de Computadoras 10"},
                    {"codigo": "RC1", "nombre": "Redes de Computadoras 1"},
                ],
                "Asistencia": [{"is_present": True}],
            }
        )

        self.run_action(
            {
                "is_authenticated": True,
                "matricula": "66001",
                "materia": "Redes de Computadoras 1",
            },
            backend,
        )

        self.assertIn(("Asistencia", "eq", "materia", "RC1"), backend.calls)

    def test_numbered_subject_resolution_defaults_and_normalizes_numerals(self):
        catalog = [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "FIS3", "nombre": "Física III"},
        ]
        cases = {
            "Física": "FIS1",
            "fisica": "FIS1",
            "FISICA": "FIS1",
            "Física 1": "FIS1",
            "Física I": "FIS1",
            "fisica i": "FIS1",
            "Física 2": "FIS2",
            "Física II": "FIS2",
            "fisica ii": "FIS2",
            "Física 3": "FIS3",
            "Física III": "FIS3",
        }

        for expression, expected_code in cases.items():
            with self.subTest(expression=expression):
                status, record = ACTION_MODULE._resolve_subject(catalog, expression)
                self.assertEqual(status, "resolved")
                self.assertEqual(record["codigo"], expected_code)
                self.assertIn(record["nombre"], {"Física I", "Física II", "Física III"})

    def test_numbered_subject_resolution_is_generic_for_algebra(self):
        catalog = [
            {"codigo": "ALG1", "nombre": "Álgebra I"},
            {"codigo": "ALG2", "nombre": "Álgebra II"},
        ]

        for expression, expected_code in {
            "algebra": "ALG1",
            "Álgebra 1": "ALG1",
            "algebra i": "ALG1",
            "algebra 2": "ALG2",
            "Álgebra II": "ALG2",
        }.items():
            with self.subTest(expression=expression):
                status, record = ACTION_MODULE._resolve_subject(catalog, expression)
                self.assertEqual(status, "resolved")
                self.assertEqual(record["codigo"], expected_code)

    def test_numbered_subject_levels_remain_distinct(self):
        catalog = [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "FIS3", "nombre": "Física III"},
        ]

        for expression, expected_code in {
            "Física I": "FIS1",
            "Física II": "FIS2",
            "Física III": "FIS3",
        }.items():
            with self.subTest(expression=expression):
                status, record = ACTION_MODULE._resolve_subject(catalog, expression)
                self.assertEqual(status, "resolved")
                self.assertEqual(record["codigo"], expected_code)

    def test_unknown_numbered_subject_is_not_invented_or_defaulted(self):
        catalog = [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "FIS3", "nombre": "Física III"},
        ]

        status, record = ACTION_MODULE._resolve_subject(catalog, "Física 4")

        self.assertEqual(status, "not_found")
        self.assertEqual(record, [])


if __name__ == "__main__":
    unittest.main()
