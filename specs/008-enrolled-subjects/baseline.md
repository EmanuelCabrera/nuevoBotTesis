# 008 — Materias cursadas / Course Records — Audit Baseline

## Audit scope

This baseline preserves the production behavior observed before the 008
contract cleanup. It is historical evidence, not a description of the aligned
implementation.

## Intent inventory

The sole course-record intent was `consultar_materias`, with 36 training
examples. Nineteen examples omit matrícula and seventeen include it. Wording
mixes:

- generic owned subjects: “quiero ver mis materias”;
- current-course claims: “mis materias en curso”;
- period claims: “este cuatrimestre” and “este semestre”;
- requests carrying a `matricula` entity.

There is no specialized intent such as `listar_materias`,
`consultar_materias_inscriptas`, or
`proporcionar_matricula_para_materias`. The shared
`proporcionar_matricula` intent supplies the required form value.

`proporcionar_materia` is unrelated to this capability because 008 lists all
rows and does not ask for a subject.

## Dialogue inventory

- Form: `materias_form`.
- Required slots: `matricula` only.
- Prompt: `utter_ask_materias_form_matricula`.
- Direct conditional rule: matrícula already set → action.
- Form activation rule: `consultar_materias` → `materias_form`.
- Form completion rule: close form → action.
- Legacy flow rule: `flujo_actual=consultar_materias` → action.
- Existing stories: eight subject-listing stories, including direct,
  form-based, greeting, matrícula-follow-up, and repeated-request variants.

The action, not the form/rules, enforces authentication.

## Action inventory

`ActionConsultarMaterias` lives in `actions/actionsMaterias.py` and exposes
`action_consultar_materias`.

Its only data query is:

```text
MateriaCursada.select(fecha_cursada, Materia(nombre))
              .eq(estudiante, matricula)
```

It does not use `SubjectCatalogRepository` or `SubjectResolver`, despite those
symbols being imported and initialized in the module for other actions.

## Exact current product semantics

The action returned all visible historical `MateriaCursada` rows for a matrícula.
It is not limited to active, current-semester, unapproved, approved, or latest
course records. Consequently, current NLU phrases such as “materias actuales”
overpromise relative to the query.

## Current defects and limitations

1. Fourteen of 36 user-facing examples implied current enrollment or a current
   academic period, while the query returned historical course rows.
2. `aprobada` exists but is not selected or filtered.
3. No active/inactive, cancellation, semester, year, or academic-period field
   is observable.
4. Invalid matrícula and valid matrícula with zero rows produce the same
   response.
5. No explicit ordering is defined.
6. No deduplication is performed and no uniqueness constraint was verifiable.
7. Authentication failure returns no cleanup events.
8. Backend failure returns no cleanup/retry-state events.
9. Success clears the unrelated `materia` slot; the empty-result path does not.
10. The legacy `flujo_actual` continuation overlaps with `materias_form`.
11. No existing dedicated action, Core, integration, or end-to-end test targets
    enrolled subjects.
12. The grades NLU suite contains only two `consultar_materias` contrasts.

## Database evidence

The audit observed 35 rows spanning 2019-08-14 to 2025-03-01. Values of
`aprobada` included `true`, `false`, and `null`. No duplicate
`(estudiante, cod_materia)` pair was observed, but the available Supabase key
cannot inspect database constraints because the OpenAPI endpoint requires
`service_role`.

## Baseline suites

The audit created initial versions of these dedicated baseline files:

- `tests/nlu_enrolled_subjects_test.yml`;
- `tests/test_enrolled_subjects_stories.yml`;
- `tests/test_action_enrolled_subjects.py`.

Those initial versions characterized behavior and defects without repairing
production behavior. They were subsequently aligned with the final contract;
see `results.md` for their current expectations and results.

## Baseline execution

Environment:

- Python 3.9.12;
- Rasa 3.6.20;
- Rasa SDK 3.6.2;
- fresh model: `/private/tmp/nuevoBotTesis_008_baseline/008_baseline.tar.gz`.

`rasa data validate` passed with only the repository's pre-existing warnings
about unused intents and utterances.

### Dedicated 008 results

- NLU: **21/24 (87.5%)** overall;
- `consultar_materias`: **8/8**, 100% precision, recall, and F1;
- `materia` entity: 100% precision, recall, and F1;
- `matricula` entity: 100% precision, recall, and F1;
- Core: **5/5 conversations**, **20/20 actions**;
- action characterization: **10/10**.

The three NLU errors were:

- “cuánto saqué en Álgebra”: `consultar_notas` → `proporcionar_materia`;
- “a qué finales estoy inscripto”: unsupported `out_of_scope` →
  `consultar_fecha_mesas_examen_final`;
- “qué tengo”: deliberately underspecified `out_of_scope` →
  `consultar_fecha_mesas_examen_final`.

The latter two expose unsupported/ambiguous boundaries; they are not evidence
that either request belongs to `consultar_materias`.

### Regression controls for capabilities 001–007

| Capability | NLU | Core conversations | Core actions |
|---|---:|---:|---:|
| Attendance | 27/28 | 4/4 | 19/19 |
| Grades | 15/18 | 5/5 | 27/27 |
| Subject requirements | 21/22 | 6/6 | 31/31 |
| Final-exam dates | 24/24 | 5/5 | 26/26 |
| Partial-exam dates | 26/27 | 5/5 | 25/25 |
| Final-exam registration | 28/28 | 5/5 | 23/23 |
| Final-exam cancellation | 18/19 | 5/5 | 20/20 |
| **Total** | **159/166** | **35/35** | **171/171** |

No regression-control error was predicted as `consultar_materias`, and no
course-record example was confused with a completed-capability intent.

### Full Python suite

The full suite produced **132/133**. The sole failure is the pre-existing,
unrelated attendance fixture mismatch in `test_no_matching_subject`: the test
expects `flujo_actual: None`, while the action returns `materia: None`.

With the new file isolated, the 008 action suite is **10/10**.

## Smallest recommended implementation step

Refactor only `ActionConsultarMaterias` around an explicit repository/query
boundary while preserving the supported contract:

```text
explicit consultar_materias
→ authentication / matrícula
→ MateriaCursada filtered by estudiante
→ related Materia.nombre
→ controlled response and consistent state cleanup
```

The subsequent product-contract verification selected historical
`MateriaCursada` course records. It explicitly rejected current-enrollment,
current-period, and approved-only semantics.
