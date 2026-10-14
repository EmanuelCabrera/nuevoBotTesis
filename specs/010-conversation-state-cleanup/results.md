# 010 — Conversation State Cleanup — Results

## Outcome

010 removes `flujo_actual` completely from runtime and current tests. Form
context is now represented by `active_loop`, `requested_slot`, and the actual
business slots. No production NLU data was changed.

All 20 acceptance criteria pass. Capability 010 is **DONE**.

## Previous state and removal

The generic slot historically identified a capability after an action had
already run. By the 010 baseline no action read it; only three conditional
rules consumed it. Attendance reactivated a form, while Requirements and
Course Records reran their action without collecting the missing value.

The cleanup removed:

- the domain entity and influential custom slot;
- the three conditional rules for Attendance, Requirements, and Course
  Records;
- every `SlotSet("flujo_actual", ...)` write and clear operation;
- legacy flow events from the production Attendance story;
- current unit/Core assertions coupled only to that state.

Production now contains zero references to `flujo_actual`.

## Form-owned subject validation

`actions/form_validators.py` introduces six concrete validators backed by the
shared `SubjectCatalogRepository` and `SubjectResolver`:

- `validate_asistencia_form`;
- `validate_notas_form`;
- `validate_requisitos_form`;
- `validate_consultar_mesas_form`;
- `validate_fechas_parciales_form`;
- `validate_cancelar_mesa_form`.

006 retains its existing `validate_inscripcion_mesa_form` implementation.
Action-server discovery was verified explicitly: all seven validators register
successfully.

A resolved expression is stored as its canonical name. Unknown and ambiguous
expressions return `materia: null`; Rasa therefore keeps the active form and
continues requesting `materia`. Ambiguity reports canonical candidates. A
catalog failure has a separate technical response and is not represented as a
missing subject. Business actions retain defensive resolution for direct or
unexpected invocation.

## Retry behavior by capability

| Capability | Final retry behavior |
|---|---|
| 001 Attendance | Unknown/ambiguous materia remains in `asistencia_form`; corrected input submits |
| 002 Grades | Unknown/ambiguous materia remains in `notas_form`; corrected input submits |
| 003 Requirements | Unknown/ambiguous materia remains in `requisitos_form`; corrected input submits |
| 004 Final dates | Unknown/ambiguous materia remains in `consultar_mesas_form`; corrected input submits |
| 005 Partial dates | Unknown/ambiguous materia remains in `fechas_parciales_form`; corrected input submits |
| 006 Registration | Existing validator continues to own subject rejection and retry |
| 007 Cancellation | Unknown/ambiguous materia remains in `cancelar_mesa_form`; corrected input submits |

The dedicated 010 Core suite covers one rejected-subject retry per applicable
flow and passes **7/7 conversations, 53/53 actions**. Unit tests separately
cover canonical, unknown, ambiguous, and catalog-error validator outcomes.

## Requirements matrícula decision

`ActionConsultarRequerimientosMateria` previously rejected a missing matrícula,
although its only business query is:

```text
MateriaEquivalencia.eq("materia_codigo", canonical_subject_code)
```

Matrícula affected neither the query, authentication, authorization, nor a
business rule. It was removed from the action dependency and was not added to
`requisitos_form`. Authentication itself remains unchanged. Historical 003
documents continue to describe their original snapshot.

## Attendance fixture

The historical `test_no_matching_subject` expectation represented obsolete
generic flow cleanup. The meaningful action assertion remains
`materia: null`; form ownership is now established by the 010 Core story,
which verifies that `requested_slot` remains `materia` and corrected input
completes the flow. The test no longer simulates recovery by manually treating
`flujo_actual` as context.

## Validation environment

- Python 3.9.12
- Rasa 3.6.20
- Rasa SDK 3.6.2
- Conda environment: `myenv`

Results:

- full Python suite: **138/138 passed**;
- `rasa data validate`: passed, no story conflicts;
- fresh training: passed for three independent full models;
- action package discovery: passed for all production actions and validators.

The validator warnings about unused intents/utterances and local font-cache
messages are pre-existing/non-functional and did not fail validation or tests.

## Core regression by capability

Run 1 dedicated results:

| Capability | Conversations | Actions |
|---|---:|---:|
| 001 Attendance | 4/4 | 19/19 |
| 002 Grades | 5/5 | 27/27 |
| 003 Requirements | 6/6 | 31/31 |
| 004 Final Exam Dates | 5/5 | 26/26 |
| 005 Partial Exam Dates | 5/5 | 25/25 |
| 006 Final Exam Registration | 5/5 | 22/22 |
| 007 Final Exam Cancellation | 5/5 | 20/20 |
| 008 Course Records | 5/5 | 20/20 |
| 009 Institutional FAQs | 19/19 | 42/42 |
| 010 Retry/state | 7/7 | 53/53 |

The complete Core set also includes three shared mesa stories. Three-run
stability was identical:

| Run | Conversations | Actions |
|---|---:|---:|
| 1 | 69/69 | 309/309 |
| 2 | 69/69 | 309/309 |
| 3 | 69/69 | 309/309 |

## NLU regression

No production NLU file or pipeline setting changed. Run 1 diagnostics were:

| Capability | Result |
|---|---:|
| 001 Attendance | 26/28 |
| 002 Grades | 15/18 |
| 003 Requirements | 20/22 |
| 004 Final Exam Dates | 24/24 |
| 005 Partial Exam Dates | 26/27 |
| 006 Final Exam Registration | 27/28 |
| 007 Final Exam Cancellation | 19/19 |
| 008 Course Records | 23/25 |
| 009 Institutional FAQs | 48/55 |

The differences from prior combined-model runs are DIET statistical variation,
not a 010 semantic change. Representative misses are the known subject-only
phrases predicted as `proporcionar_materia`, cross-capability date ambiguity,
and the six deliberately generic 009 diagnostics. No NLU examples were edited
to chase those scores.

## Remaining references

Repository-wide search finds no reference in production or current tests.
Remaining matches are documentation only:

- 010 specification, baseline, acceptance, and this result explain the removed
  mechanism;
- 003–009 specifications/baselines/results preserve the architecture and test
  outcomes that existed when each earlier capability was completed.

Those historical records were intentionally not rewritten.

## Deferred concerns

- post-completion elliptical follow-ups such as “¿y en Física?”;
- generic fallback/help behavior;
- ambiguous generic date clarification such as “fecha de Física II”;
- partial number/type/recuperatorio support;
- global matrícula/authentication architecture cleanup;
- registration re-enrollment policy after `baja=true`.

## Suggested commit

```text
refactor(010): eliminar flujo_actual y delegar reintentos a formularios
```
