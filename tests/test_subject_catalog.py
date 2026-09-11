"""Tests for the runtime subject catalog and pure subject resolver."""

import unittest

from actions.subject_catalog import SubjectCatalogRepository
from actions.subject_resolver import SubjectResolver


class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, backend):
        self.backend = backend

    def select(self, fields):
        self.backend.select_fields.append(fields)
        return self

    def execute(self):
        self.backend.fetches += 1
        if self.backend.error:
            raise self.backend.error
        return _Response(self.backend.rows)


class _CatalogClient:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.fetches = 0
        self.select_fields = []

    def table(self, name):
        self.asserted_table = name
        return _Query(self)


class SubjectCatalogRepositoryTests(unittest.TestCase):
    def test_first_call_fetches_full_catalog(self):
        client = _CatalogClient([{"codigo": "FIS1", "nombre": "Física I"}])
        repository = SubjectCatalogRepository(client, ttl_seconds=600, clock=lambda: 0)

        subjects = repository.get_subjects()

        self.assertEqual(subjects, [{"codigo": "FIS1", "nombre": "Física I"}])
        self.assertEqual(client.fetches, 1)
        self.assertEqual(client.asserted_table, "Materia")
        self.assertEqual(client.select_fields, ["codigo, nombre"])

    def test_second_call_within_ttl_uses_cache(self):
        now = [10]
        client = _CatalogClient([{"codigo": "FIS1", "nombre": "Física I"}])
        repository = SubjectCatalogRepository(client, ttl_seconds=600, clock=lambda: now[0])

        repository.get_subjects()
        now[0] = 609
        subjects = repository.get_subjects()

        self.assertEqual(subjects[0]["codigo"], "FIS1")
        self.assertEqual(client.fetches, 1)

    def test_call_after_ttl_refreshes_catalog(self):
        now = [10]
        client = _CatalogClient([{"codigo": "FIS1", "nombre": "Física I"}])
        repository = SubjectCatalogRepository(client, ttl_seconds=600, clock=lambda: now[0])

        repository.get_subjects()
        client.rows = [{"codigo": "FIS2", "nombre": "Física II"}]
        now[0] = 610
        subjects = repository.get_subjects()

        self.assertEqual(subjects, [{"codigo": "FIS2", "nombre": "Física II"}])
        self.assertEqual(client.fetches, 2)

    def test_fetch_failure_does_not_fabricate_subjects(self):
        client = _CatalogClient(error=RuntimeError("backend unavailable"))
        repository = SubjectCatalogRepository(client, ttl_seconds=600, clock=lambda: 0)

        with self.assertRaises(RuntimeError):
            repository.get_subjects()

        self.assertEqual(client.fetches, 1)


class SubjectResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = SubjectResolver()
        self.catalog = [
            {"codigo": "FIS1", "nombre": "Física I"},
            {"codigo": "FIS2", "nombre": "Física II"},
            {"codigo": "FIS3", "nombre": "Física III"},
            {"codigo": "ALG1", "nombre": "Álgebra I"},
            {"codigo": "ALG2", "nombre": "Álgebra II"},
        ]

    def test_resolves_normalized_numbered_subjects_without_inventing(self):
        expected = {
            "fisica": "FIS1",
            "fisica 2": "FIS2",
            "fisica iii": "FIS3",
            "algebra": "ALG1",
            "algebra 2": "ALG2",
        }

        for expression, code in expected.items():
            with self.subTest(expression=expression):
                status, record = self.resolver.resolve(self.catalog, expression)
                self.assertEqual(status, "resolved")
                self.assertEqual(record["codigo"], code)

        self.assertEqual(self.resolver.resolve(self.catalog, "fisica 4"), ("not_found", []))

    def test_preserves_canonical_identity_and_distinct_levels(self):
        status, record = self.resolver.resolve(self.catalog, "FISICA II")

        self.assertEqual(status, "resolved")
        self.assertEqual(record, {"codigo": "FIS2", "nombre": "Física II"})

    def test_ambiguity_is_returned_without_arbitrary_selection(self):
        catalog = [
            {"codigo": "FISA", "nombre": "Física Aplicada"},
            {"codigo": "FISE", "nombre": "Física Experimental"},
        ]

        status, records = self.resolver.resolve(catalog, "Física")

        self.assertEqual(status, "ambiguous")
        self.assertEqual({row["codigo"] for row in records}, {"FISA", "FISE"})


if __name__ == "__main__":
    unittest.main()
