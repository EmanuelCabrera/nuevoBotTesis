# 007 — Final Exam Registration Cancellation — Baseline

## Current implementation

The capability is implemented by `ActionCancelarInscripcionMesa` in
`actions/actionsMesaExamen.py`.

The form is `cancelar_mesa_form` with required slots:

- `matricula`
- `materia`

The intent `cancelar_inscripcion_mesa_examen` has 35 training examples. There
is no cancellation-specific subject-follow-up intent. Generic
`proporcionar_materia` is used by the current form stories.

The action currently performs:

```text
Materia.ilike(nombre, "%materia%") → first row
→ MesaExamen by materia_codigo
→ Inscripcion by estudiante + codigo_mesa
→ delete matching rows
```

It does not use `SubjectCatalogRepository` or `SubjectResolver`, does not
filter `baja=false`, and does not update `baja`.

## Database contract observed

`Inscripcion` contains `id`, `created_at`, `codigo_mesa`, `estudiante`,
`baja`, and `fecha_inscripcion`. `codigo_mesa` relates to `MesaExamen.codigo`,
and `MesaExamen.materia_codigo` relates to `Materia.codigo`.

The current action physically deletes matching rows. No cancellation timestamp
or separate cancellation record is used by the implementation. Capability 006
checks any existing row when preventing duplicate registration, including
`baja=true`; re-registration after cancellation is therefore a deferred
product-policy question.

## NLU baseline

Held-out dataset: `tests/nlu_final_exam_cancellation_test.yml`.

The dataset contains explicit cancellation requests, registration/date/partial
contrasts, and subject-only form replies. Metrics are measured below after the
fresh local training run.

Fresh local model: `models/007_baseline.tar.gz`.

- Overall: **16/19 (84.2%)**.
- `cancelar_inscripcion_mesa_examen`: **P 100% / R 62.5% / F1 76.9%**.
- `inscribirse_mesa_examen`: **P 60% / R 100% / F1 75.0%**.
- `consultar_fecha_mesas_examen_final`: **P 75% / R 100% / F1 85.7%**.
- `consultar_fechas_parciales`: **P/R/F1 100%**.
- `proporcionar_materia`: **P/R/F1 100%**.
- `materia` entity: **P/R/F1 100% / 100% / 100%**.

The three cancellation misses were:

| Held-out text | Expected | Prediction |
|---|---|---|
| necesito dar de baja la mesa de Álgebra y Geometría Analítica | cancellation | final-date consultation |
| desanotame de la mesa de Análisis Matemático II | cancellation | registration |
| quiero anular mi inscripción para Algoritmos y Estructuras II | cancellation | registration |

These are semantic-boundary failures, not entity-extraction failures.

## Dialogue baseline

Characterization stories cover explicit cancellation with and without subject,
generic subject follow-up, no-registration completion, and repeated explicit
requests. Results are recorded after the fresh Core run.

Fresh Core result:

- **5/5 conversations**;
- **100% action prediction accuracy**;
- no failed stories.

## Action baseline

The dedicated action tests intentionally characterize both current behavior and
spec gaps, including:

- authentication/matrícula prerequisites;
- successful deletion of matching rows;
- no matching registration;
- already-cancelled rows being treated like any other matching row;
- multiple matching registrations;
- invalid subject and no-mesa outcomes;
- backend failures;
- characterization of canonical numbered-resolution and ambiguity gaps.

Fresh action result:

- **12/12 characterization tests passing**.

The tests record that numbered input is not canonically resolved and an
ambiguous expression selects the first matching subject. They also record that
matching rows with `baja=true` are physically deleted and that multiple
matching registrations are cancelled together.

## Python and regression controls

The full suite after adding the characterization tests ran **115 tests**:

- **114 passing**;
- **1 unrelated failure**, `test_no_matching_subject` in attendance, where the
  fixture expects `flujo_actual: None` and production emits `materia: None`.

Representative NLU controls using the same fresh model:

| Capability | Result | Notable issue |
|---|---:|---|
| Attendance | 27/28 | one historical elliptical follow-up classified as `proporcionar_materia` |
| Grades | 15/18 | three pre-existing grades/attendance boundary errors |
| Requirements | 21/22 | one final-date/partial boundary error |
| Final dates | 23/24 | one generic “presentarme a rendir” classified as `plazos_inscripcion` |
| Partial dates | 27/27 | no errors |
| Registration | 28/28 | cancellation and registration contrasts correct in this control |

## Acceptance baseline

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PARTIAL | Explicit cancellation is recognized in Core, but dedicated NLU recall is 62.5%. |
| AC-02 | PASS | Missing-subject form path passes in Core. |
| AC-03 | PASS | Generic `proporcionar_materia` follow-up passes in Core. |
| AC-04 | FAIL | Current action uses `ILIKE` and does not canonically resolve numbered subjects. |
| AC-05 | PASS | Invalid subject is reported without a mesa query. |
| AC-06 | FAIL | Current action selects the first matching subject. |
| AC-07 | PASS | No matching registration is reported separately. |
| AC-08 | PASS | Matching registration rows are cancelled by the current contract. |
| AC-09 | PASS | Current `baja=true` behavior is characterized: the row is deleted. |
| AC-10 | PASS | Multiple matching rows are cancelled together and counted. |
| AC-11 | PASS | Successful deletion produces confirmation. |
| AC-12 | PASS | Registration remains a separate intent and Core path. |
| AC-13 | PASS | Backend failure produces a controlled error. |
| AC-14 | FAIL | The action returns no cleanup events for materia/flujo_actual. |
| AC-15 | PARTIAL | Final-date examples are recognized, but one cancellation false-positive crosses the boundary. |
| AC-16 | PARTIAL | The form requests matrícula, but the action itself does not check authentication. |
| AC-17 | PASS | Re-registration after cancellation is documented as deferred and unchanged. |

## Known gaps

1. Subject lookup is substring-based and selects the first result.
2. Arabic/Roman numbered subjects are not resolved canonically.
3. Ambiguous subjects are not surfaced for clarification.
4. `baja` is ignored and matching rows are deleted physically.
5. The action does not independently verify authentication.
6. Returned events do not clear cancellation slots or `flujo_actual`.
7. Multiple matching registrations are cancelled in one request.
