# 006 — Final Exam Registration — Pre-Refactor Baseline

This document records the current registration behavior before the production
refactor. It is historical evidence and must not be rewritten after the
implementation changes.

## Test environment and measurement limits

- Host Python: 3.13.5
- Project-compatible Rasa environment expected from previous capabilities:
  Rasa 3.6.20, rasa-sdk 3.6.2, spaCy 3.7.2
- No compatible local Rasa installation was available on the host.
- Docker evaluation was not executable because the Docker daemon was not
  running.
- Therefore the NLU and Core dialogue metrics are **NOT MEASURED** in this
  baseline run. The dedicated files were created for the compatible Rasa
  environment and should be executed there.

## Current intent architecture

- Main registration intent: `inscribirse_mesa_examen` — 62 training examples.
- Specialized intent: `proporcionar_materia_para_inscripcion` — 18 examples.
- Table selection intent: `seleccionar_mesa_examen` — 18 examples.
- Cancellation intent: `cancelar_inscripcion_mesa_examen` — 37 examples.

All 18 examples under `proporcionar_materia_para_inscripcion` are complete
registration requests, such as “La materia para inscribirme es matemática”
and “Quiero inscribirme a la mesa de física”. None is a true subject-only
reply. The specialized intent is therefore a historical label and creates an
unnecessary semantic boundary, although the current rule still depends on it.

## Form and dialogue baseline

The current production flow is:

```text
inscribirse_mesa_examen
→ inscripcion_mesa_form (matricula, materia)
→ action_ofrecer_mesas_examen
→ seleccionar_mesa_form (fecha_mesa or codigo_mesa_examen)
→ action_inscripcion_mesa_examen
```

The rules explicitly continue the form after
`proporcionar_materia_para_inscripcion`. There is no dedicated rule for the
generic `proporcionar_materia` intent in this flow.

Dedicated characterization stories were created in
`tests/test_final_exam_registration_stories.yml`, including both the current
specialized follow-up and a generic follow-up. They were not executed because
the local Rasa/Docker runtime was unavailable.

## Action baseline

Dedicated suite: `tests/test_action_final_exam_registration.py`.

- Passing: **15/17**
- Failing: **2/17**

Passing behavior includes authentication and matrícula checks, table listing,
one and multiple available tables, no-table messaging, invalid table codes,
duplicate detection, insertion, date-based table selection, and controlled
backend errors.

### Expected contract failures

1. `fisica 2` is sent to `Materia.ilike` and does not resolve to canonical
   `Física II` / its canonical code.
2. An ambiguous `Física` expression selects the first partial match and
   queries `MesaExamen` instead of asking for clarification.

The current registration actions do not use `SubjectCatalogRepository` or
`SubjectResolver`. `ActionOfrecerMesasExamen` uses `ILIKE` and the first row;
`ActionInscripcionMesaExamen` repeats that lookup when a date is supplied.

## Supabase data contract observed

Read-only inspection of the live database found:

### `MesaExamen`

Observed columns:

- `codigo`
- `created_at`
- `fecha`
- `materia_codigo`
- `presidente`
- `primer_vocal`

There are **8** rows. `materia_codigo` joins to `Materia.codigo`.

### `Inscripcion`

Observed columns:

- `id`
- `created_at`
- `codigo_mesa`
- `estudiante`
- `baja`
- `fecha_inscripcion`

There are **35** rows: 29 with `baja=false` and 6 with `baja=true`.
`codigo_mesa` joins to `MesaExamen.codigo`. The application uses
`estudiante` as the matrícula identifier. PostgREST exposes an `Estudiante`
relationship, but the queried table returned no rows, so the exact target
column for that relation could not be confirmed with the available key.

One duplicate active pair was observed for `(estudiante=66003,
codigo_mesa=cod1008)`. No uniqueness constraint was established from the
available read-only API. The action performs an application-level duplicate
check but does not filter by `baja`.

## Registration semantics currently implemented

The implementation requires authentication and matrícula, lists tables for a
subject, accepts a table code or date, checks for an existing registration,
and inserts an `Inscripcion` row. It does **not** validate:

- correlatives or prerequisite approval;
- grades, attendance, or `MateriaCursada` eligibility;
- registration periods or deadlines;
- capacity, availability status, or exam eligibility;
- academic periods or exam types.

When multiple tables exist, all are displayed and the selection form requests
a date or code. Even a single table is not automatically registered.

## NLU baseline

Held-out dataset: `tests/nlu_final_exam_registration_test.yml`.

- Dataset created: **28 examples**.
- NLU accuracy: **NOT MEASURED** (Rasa runtime unavailable).
- `inscribirse_mesa_examen` precision/recall/F1: **NOT MEASURED**.
- `materia` entity precision/recall/F1: **NOT MEASURED**.

The dataset includes explicit registration requests, final-date, partial-date,
cancellation, requirements, grades, attendance, and subject-only contrasts.

## Dialogue baseline

- Dedicated registration conversations: **NOT MEASURED**.
- Action predictions: **NOT MEASURED**.

The stories characterize:

- explicit request with subject and matrícula;
- missing data and form activation;
- current specialized subject follow-up;
- generic subject follow-up as a likely current routing gap;
- table selection by date;
- table selection by code.

## Python baseline and regression controls

```text
python3 -m unittest discover -s tests -p 'test_*.py'
```

- Total: **96**
- Passed: **93**
- Failed: **3**

Failures:

- 2 intentional 006 characterization failures for canonical numbered
  resolution and ambiguity handling;
- 1 unrelated historical attendance fixture mismatch:
  `test_no_matching_subject` expects `flujo_actual: None`, while the current
  attendance action emits `materia: None`.

The existing Python action tests for attendance, grades, requirements, final
dates, partial dates, and subject resolution otherwise remain green.

## Acceptance baseline

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PARTIAL | Existing stories define the flow, but end-to-end Core was not measured and the action still uses legacy lookup. |
| AC-02 | PARTIAL | Form requires the missing data, but no fresh Core run was available. |
| AC-03 | PARTIAL | Specialized follow-up rule exists; generic `proporcionar_materia` has no dedicated registration rule. |
| AC-04 | FAIL | Registration actions do not use the shared canonical resolver; numbered expressions fail the characterization test. |
| AC-05 | PASS | Invalid subject is reported and no table is listed by the current action test. |
| AC-06 | FAIL | Ambiguous subject selects the first `ILIKE` result. |
| AC-07 | PARTIAL | No-table messaging works, but cleanup and retry semantics are not explicit. |
| AC-08 | PARTIAL | A single table is listed and can be selected, but no Core verification was available. |
| AC-09 | PASS | Multiple rows are listed and selection is deferred to the selection form. |
| AC-10 | PASS | Code/date selection and table validation are covered by characterization tests. |
| AC-11 | PASS | A selected table produces an `Inscripcion` insert in the action test. |
| AC-12 | PARTIAL | Duplicate detection exists, but `baja` semantics and database uniqueness are unresolved. |
| AC-13 | PASS | Cancellation has a distinct intent, form, and action. |
| AC-14 | PASS | Catalog, mesa, and insert exceptions produce controlled messages in action tests. |
| AC-15 | PARTIAL | Final registration clears state, but offering/no-table branches retain state inconsistently. |
| AC-16 | NOT MEASURED | Training data contains the boundary, but fresh NLU evaluation was unavailable. |
| AC-17 | PASS | Authentication and matrícula prerequisites are enforced by forms/actions and unit tests. |

## Known implementation gaps

- duplicated complete-request examples under
  `proporcionar_materia_para_inscripcion`;
- no generic subject-follow-up rule for the active registration form;
- `ILIKE` plus first-result subject lookup;
- no shared canonical subject resolver in registration actions;
- no ambiguity outcome before table queries;
- inconsistent slot cleanup on no-table/lookup failures;
- duplicate detection does not distinguish active and cancelled rows;
- no confirmed database uniqueness constraint for student/table pairs;
- no dedicated registration action tests existed before this baseline;
- NLU/Core metrics remain unmeasured in this environment.

## Recommended refactor order

1. Reuse `SubjectCatalogRepository` and `SubjectResolver` in both registration
   lookup paths.
2. Separate resolved, not-found, ambiguous, and no-table outcomes.
3. Make the active form use contextual generic subject provision, if the Core
   characterization confirms it is safe.
4. Preserve explicit table selection by date/code.
5. Define active/cancelled duplicate semantics before changing persistence.
6. Add a fresh compatible Rasa NLU/Core run and regression controls.
