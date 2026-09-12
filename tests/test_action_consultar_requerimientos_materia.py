"""Characterization tests for the legacy subject-requirements action."""

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
    def utter_message(self, text=None, **kwargs): self.messages.append(text if text is not None else kwargs.get("text"))
class _SlotSet:
    def __init__(self, key, value): self.key, self.value = key, value


def _load_module():
    rasa_sdk = types.ModuleType("rasa_sdk"); rasa_sdk.Action = _Action; rasa_sdk.Tracker = _Tracker
    executor = types.ModuleType("rasa_sdk.executor"); executor.CollectingDispatcher = _Dispatcher
    events = types.ModuleType("rasa_sdk.events"); events.SlotSet = _SlotSet
    dotenv = types.ModuleType("dotenv"); dotenv.load_dotenv = lambda: None
    supabase = types.ModuleType("supabase"); supabase.Client = object; supabase.create_client = lambda *_: object()
    httpx = types.ModuleType("httpx")
    modules = {"rasa_sdk": rasa_sdk, "rasa_sdk.executor": executor, "rasa_sdk.events": events,
               "dotenv": dotenv, "supabase": supabase, "httpx": httpx}
    path = Path(__file__).parents[1] / "actions" / "actionsMaterias.py"
    spec = importlib.util.spec_from_file_location("requirements_actions_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules): spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, data): self.data = data


class _Query:
    def __init__(self, backend, table): self.backend, self.table, self.filters = backend, table, []
    def select(self, fields): self.backend.calls.append((self.table, "select", fields)); return self
    def ilike(self, column, value): self.backend.calls.append((self.table, "ilike", column, value)); self.filters.append((column, value)); return self
    def eq(self, column, value): self.backend.calls.append((self.table, "eq", column, value)); return self
    def execute(self):
        if self.table in self.backend.errors: raise self.backend.errors[self.table]
        rows = list(self.backend.rows.get(self.table, []))
        for column, pattern in self.filters:
            needle = pattern.strip("%").casefold()
            rows = [row for row in rows if needle in str(row.get(column, "")).casefold()]
        return _Response(rows)


class _Backend:
    def __init__(self, rows=None, errors=None, materia=None):
        self.rows, self.errors, self.calls = rows or {}, errors or {}, []
        self.rows.setdefault("Materia", materia or [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "ALG", "nombre": "Álgebra y Geometría Analítica"},
        ])
    def table(self, name): self.calls.append((name, "table")); return _Query(self, name)


ACTION_MODULE = _load_module()


def _events(events): return {(e.key, e.value) for e in events}


class RequirementsActionCharacterizationTests(unittest.TestCase):
    def setUp(self): self.action, self.dispatcher = ACTION_MODULE.ActionConsultarRequerimientosMateria(), _Dispatcher()
    def run_action(self, slots, backend):
        ACTION_MODULE.supabase = backend
        return self.action.run(self.dispatcher, _Tracker(slots), {})

    def test_successful_lookup_returns_one_direct_requirement_and_canonical_names(self):
        b = _Backend({"MateriaEquivalencia": [{"equivalencia_codigo": "FIS1", "Materia": {"nombre": "Física I"}}]})
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Física II"}, b)
        out = "\n".join(self.dispatcher.messages)
        self.assertIn("FÍSICA II", out); self.assertIn("Física I", out)
        self.assertIn(("MateriaEquivalencia", "eq", "materia_codigo", "FIS2"), b.calls)

    def test_multiple_direct_requirements_are_all_returned(self):
        b = _Backend({"MateriaEquivalencia": [
            {"equivalencia_codigo": "FIS1", "Materia": {"nombre": "Física I"}},
            {"equivalencia_codigo": "ALG", "Materia": {"nombre": "Álgebra y Geometría Analítica"}},
        ]})
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Física II"}, b)
        out = "\n".join(self.dispatcher.messages)
        self.assertIn("Física I", out); self.assertIn("Álgebra y Geometría Analítica", out)

    def test_authentication_is_required(self):
        b = _Backend(); self.run_action({"is_authenticated": False, "matricula": "66007", "materia": "fisica"}, b)
        self.assertIn("Necesitas estar autenticado", self.dispatcher.messages[0])

    def test_matricula_is_required_and_flow_is_preserved(self):
        b = _Backend(); events = self.run_action({"is_authenticated": True, "materia": "fisica"}, b)
        self.assertIn("No tengo tu número de matrícula", self.dispatcher.messages[0])
        self.assertIn(("flujo_actual", "consultar_requerimientos_materia"), _events(events))

    def test_materia_is_required_and_flow_is_preserved(self):
        b = _Backend(); events = self.run_action({"is_authenticated": True, "matricula": "66007"}, b)
        self.assertIn("No tengo la materia especificada", self.dispatcher.messages[0])
        self.assertIn(("flujo_actual", "consultar_requerimientos_materia"), _events(events))

    def test_valid_subject_with_no_requirements_is_distinct(self):
        b = _Backend({"MateriaEquivalencia": []}, materia=[{"codigo": "FIS2", "nombre": "Física II"}])
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Física II"}, b)
        self.assertIn("No se encontraron requerimientos", self.dispatcher.messages[0])

    def test_invalid_subject_is_not_no_requirements(self):
        b = _Backend({"Materia": [], "MateriaEquivalencia": []})
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Materia inexistente"}, b)
        self.assertIn("No se encontró la materia", self.dispatcher.messages[0])

    def test_backend_exception_is_controlled(self):
        b = _Backend(errors={"MateriaEquivalencia": RuntimeError("backend unavailable")})
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Física II"}, b)
        self.assertIn("Hubo un error al consultar los requerimientos", self.dispatcher.messages[0])

    def test_numbered_variant_should_resolve_to_canonical_subject(self):
        b = _Backend({"MateriaEquivalencia": [{"equivalencia_codigo": "FIS1", "Materia": {"nombre": "Física I"}}]})
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "fisica 2"}, b)
        self.assertIn(("MateriaEquivalencia", "eq", "materia_codigo", "FIS2"), b.calls)

    def test_ambiguous_subject_must_not_select_first_result(self):
        b = _Backend({"MateriaEquivalencia": []}, materia=[
            {"codigo": "F1", "nombre": "Física Aplicada"},
            {"codigo": "F2", "nombre": "Física Experimental"},
        ])
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Física"}, b)
        self.assertFalse(any(c[:2] == ("MateriaEquivalencia", "table") for c in b.calls))

    def test_success_clears_materia_and_flow(self):
        b = _Backend({"MateriaEquivalencia": [{"equivalencia_codigo": "FIS1", "Materia": {"nombre": "Física I"}}]})
        events = self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Física II"}, b)
        self.assertIn(("materia", None), _events(events)); self.assertIn(("flujo_actual", None), _events(events))

    def test_only_direct_relationships_are_returned(self):
        b = _Backend({"MateriaEquivalencia": [{"equivalencia_codigo": "FIS1", "Materia": {"nombre": "Física I"}}]})
        self.run_action({"is_authenticated": True, "matricula": "66007", "materia": "Física II"}, b)
        self.assertEqual(sum(c[:2] == ("MateriaEquivalencia", "table") for c in b.calls), 1)


if __name__ == "__main__": unittest.main()
