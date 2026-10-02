# 006 — Final Exam Registration — Final Results

## Baseline

The pre-refactor characterization recorded 15/17 action checks. The two
contract failures were canonical numbered-subject resolution (`fisica 2`) and
arbitrary first-match selection for ambiguous subjects. The pre-cleanup NLU
baseline later measured 26/28 examples; the registration intent recalled
10/11 cases and the remaining failures were registration/cancellation
boundary cases.

The historical baseline is preserved in `baseline.md`.

## Action implementation

`ActionOfrecerMesasExamen` and `ActionInscripcionMesaExamen` now resolve a
subject through the shared infrastructure:

```text
SubjectCatalogRepository
→ SubjectResolver
→ canonical Materia.codigo
→ MesaExamen query
```

The registration path no longer uses `Materia.ilike(...)` followed by an
arbitrary first result. Arabic/Roman numbering, accent/case normalization and
the resolver's existing unnumbered-family behavior are reused without
duplicating normalization or aliases.

Resolution outcomes are separated:

- `resolved`: query `MesaExamen` by canonical `materia_codigo`;
- `not_found`: report the invalid subject and do not query tables;
- `ambiguous`: show the matching canonical choices and do not query tables;
- catalog/table errors: return a controlled retryable error.

When a selected table is registered with a subject in state, the action also
checks that `MesaExamen.materia_codigo` matches the resolved canonical subject.
An unrelated table is rejected before persistence.

## Available-table and selection behavior

All available tables for the canonical subject are listed in deterministic
date order. Zero tables is reported separately from an invalid subject. A
single table is still selected through the existing selection form; it is not
automatically registered. Multiple tables remain explicit user choices by
date or code.

The selected code is looked up before insertion. Date selection resolves the
date within the canonical subject. Unknown codes, unavailable dates, and
lookup failures do not create a registration.

## Registration and duplicate semantics

The existing application policy was preserved: a row for the same
`estudiante` and `codigo_mesa` is treated as a duplicate, regardless of the
current value of `baja`. Therefore a prior cancelled row (`baja=true`) still
blocks a new registration under the current implementation. This behavior is
covered as characterization evidence; 006 does not invent a re-registration
policy or alter live data.

The insert keeps the existing contract:

```text
estudiante
codigo_mesa
fecha_inscripcion = now()
```

No eligibility, prerequisite, attendance, grade, capacity, deadline, or
academic-period checks were added. No database uniqueness constraint was
assumed.

## State cleanup

Successful registration and confirmed duplicate responses clear `materia`,
`codigo_mesa_examen`, `fecha_mesa`, and `flujo_actual`. Invalid or ambiguous
subjects clear the unresolved subject while preserving the registration flow
for retry. Catalog, table, and insert failures return controlled errors and
retain the minimum retry context rather than claiming success.

## Verification

Dedicated action suite:

```text
python3 -m unittest tests/test_action_final_exam_registration.py
26/26 passing
```

The suite covers authentication/matrícula, canonical exact and numbered
subjects, accents/case, unknown levels, ambiguity, no tables, one and multiple
tables, catalog/MesaExamen/insert failures, subject-to-table validation,
duplicate behavior including `baja=true`, date/code selection, and cleanup.

Full Python suite:

```text
python3 -m unittest discover -s tests -p 'test_*.py'
104/105 passing
```

The sole failure is the pre-existing attendance fixture mismatch in
`test_no_matching_subject`: the fixture expects `flujo_actual: None`, while
the current attendance action emits `materia: None`. It is unrelated to 006
and was not changed here.

## NLU and Core verification

The compatible local environment was used for a fresh model and three
independent closure trainings. The dedicated registration dataset contains 28
held-out examples.

| Run | Overall | Registration P/R/F1 | Cancellation P/R/F1 | Materia P/R/F1 |
|---|---:|---:|---:|---:|
| 1 | 28/28 | 100/100/100 | 100/100/100 | 100/100/100 |
| 2 | 28/28 | 100/100/100 | 100/100/100 | 100/100/100 |
| 3 | 28/28 | 100/100/100 | 100/100/100 | 98.46/100/99.22 |

Final-date, partial-date, and subject-only contrast cases were correct in all
three dedicated runs. No intent errors remained in the dedicated registration
dataset.

Core verification with the closure model passed:

- registration: 5/5 conversations, 23/23 action predictions;
- attendance: 4/4;
- grades: 5/5;
- requirements: 6/6;
- final-exam dates: 5/5;
- partial-exam dates: 5/5.

The separate cross-capability NLU controls are diagnostic only and retain
known combined-model fluctuations in historical suites: attendance 27/28,
grades 14/18, requirements 21/22, final dates 23/24, and partial dates 27/27
in the representative closure run. Their failures are outside the
registration changes; the corresponding Core regression suites remained
green.

## Specialized subject intent cleanup

The audit confirmed that all 18 examples previously labeled
`proporcionar_materia_para_inscripcion` were complete registration requests;
none was a subject-only response. They were moved into
`inscribirse_mesa_examen` (retaining useful phrasing and avoiding the one exact
duplicate already present) and the specialized intent was removed from the
functional architecture.

The final conversational design is:

```text
explicit registration request
→ inscribirse_mesa_examen
→ inscripcion_mesa_form

form requests materia
→ proporcionar_materia
→ form continues
```

The specialized intent was removed from `domain.yml`, `data/rules.yml`,
`data/stories.yml`, and the registration characterization stories. Historical
mentions in older 005/006 documentation are retained as historical evidence.

## Acceptance status

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PASS | Dedicated NLU and Core registration flow pass. |
| AC-02 | PASS | Missing-subject form path passes in Core. |
| AC-03 | PASS | Generic `proporcionar_materia` follow-up passes in Core. |
| AC-04 | PASS | Canonical and Arabic/Roman numbered resolution pass in 26/26 action tests. |
| AC-05 | PASS | Invalid subject is separated from table lookup. |
| AC-06 | PASS | Ambiguity asks for clarification without selecting a first match. |
| AC-07 | PASS | No-table outcome is distinct and tested. |
| AC-08 | PASS | Single-table selection and validation pass. |
| AC-09 | PASS | Multiple tables are offered for explicit selection. |
| AC-10 | PASS | Code/date selection validates the selected mesa. |
| AC-11 | PASS | Successful insert is covered by action tests and Core. |
| AC-12 | PASS | Current duplicate policy is enforced, including `baja=true`. |
| AC-13 | PASS | Cancellation remains a separate intent/capability boundary. |
| AC-14 | PASS | Catalog, table, and persistence failures are controlled. |
| AC-15 | PASS | Successful and duplicate outcomes clear transient registration state. |
| AC-16 | PASS | Dedicated contrasts separate registration from final-date requests. |
| AC-17 | PASS | Authentication and matrícula prerequisites are preserved. |

The policy question of whether a cancelled registration should permit a later
re-registration remains deferred; changing it is outside this feature.

## Final status

The registration capability is complete according to the current contract.
Its dedicated NLU/Core behavior is stable, the generic subject follow-up works
inside the active form, and the action layer uses canonical subject identity.
The known attendance fixture mismatch and cross-capability NLU fluctuations
must be handled in their own follow-up work and do not block 006.
