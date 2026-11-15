"""Unit tests for the shared form-owned subject validation contract."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class _FormValidationAction:
    pass


class _Tracker:
    pass


class _Dispatcher:
    def __init__(self):
        self.messages = []

    def utter_message(self, text=None, **kwargs):
        self.messages.append(text if text is not None else kwargs.get("text"))


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, backend):
        self.backend = backend

    def select(self, _fields):
        return self

    def execute(self):
        if self.backend.error:
            raise self.backend.error
        return _Response(self.backend.rows)


class _Backend:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error

    def table(self, _name):
        return _Query(self)


def _load_module():
    rasa_sdk = types.ModuleType("rasa_sdk")
    rasa_sdk.FormValidationAction = _FormValidationAction
    rasa_sdk.Tracker = _Tracker
    executor = types.ModuleType("rasa_sdk.executor")
    executor.CollectingDispatcher = _Dispatcher
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda: None
    supabase = types.ModuleType("supabase")
    supabase.Client = object
    supabase.create_client = lambda *_: object()
    modules = {
        "rasa_sdk": rasa_sdk,
        "rasa_sdk.executor": executor,
        "dotenv": dotenv,
        "supabase": supabase,
    }
    path = Path(__file__).parents[1] / "actions" / "form_validators.py"
    spec = importlib.util.spec_from_file_location("form_validators_under_test", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


MODULE = _load_module()


class SubjectFormValidatorTests(unittest.TestCase):
    def setUp(self):
        self.dispatcher = _Dispatcher()

    def configure(self, rows=None, error=None):
        MODULE.supabase = _Backend(rows, error)
        MODULE.subject_catalog = MODULE.SubjectCatalogRepository(
            lambda: MODULE.supabase, ttl_seconds=600
        )

    def validate(self, value):
        validator = MODULE.ValidateAsistenciaForm()
        return validator.validate_materia(
            value, self.dispatcher, _Tracker(), {}
        )

    def test_all_subject_forms_expose_their_expected_validation_action(self):
        expected = {
            MODULE.ValidateAsistenciaForm: "validate_asistencia_form",
            MODULE.ValidateNotasForm: "validate_notas_form",
            MODULE.ValidateRequisitosForm: "validate_requisitos_form",
            MODULE.ValidateConsultarMesasForm: "validate_consultar_mesas_form",
            MODULE.ValidateFechasParcialesForm: "validate_fechas_parciales_form",
            MODULE.ValidateCancelarMesaForm: "validate_cancelar_mesa_form",
        }
        self.assertEqual(
            {validator().name() for validator in expected}, set(expected.values())
        )

    def test_valid_subject_is_stored_with_canonical_name(self):
        self.configure([
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
        ])
        self.assertEqual(self.validate("fisica 2"), {"materia": "Física II"})
        self.assertEqual(self.dispatcher.messages, [])

    def test_unknown_subject_is_cleared_for_retry(self):
        self.configure([{"codigo": "FIS1", "nombre": "Física I"}])
        self.assertEqual(self.validate("Astrofísica"), {"materia": None})
        self.assertIn("No se encontró", self.dispatcher.messages[0])

    def test_ambiguous_subject_is_cleared_and_lists_candidates(self):
        self.configure([
            {"codigo": "FISA", "nombre": "Física Aplicada"},
            {"codigo": "FISE", "nombre": "Física Experimental"},
        ])
        self.assertEqual(self.validate("Física"), {"materia": None})
        output = self.dispatcher.messages[0]
        self.assertIn("varias materias", output)
        self.assertIn("Física Aplicada", output)
        self.assertIn("Física Experimental", output)

    def test_catalog_failure_is_technical_and_retryable(self):
        self.configure(error=RuntimeError("catalog unavailable"))
        self.assertEqual(self.validate("Física"), {"materia": None})
        self.assertIn("error al consultar el catálogo", self.dispatcher.messages[0])
        self.assertNotIn("No se encontró", self.dispatcher.messages[0])


if __name__ == "__main__":
    unittest.main()

