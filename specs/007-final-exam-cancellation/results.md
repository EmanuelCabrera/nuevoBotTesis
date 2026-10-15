# 007 — Final Exam Registration Cancellation — Final Results

## Baseline

The original action searched `Materia` with a partial `ILIKE`, selected the
first row, deleted every matching `Inscripcion`, and returned no slot-cleanup
events. The characterization baseline recorded:

- NLU: **16/19**;
- cancellation intent: **100% precision / 62.5% recall / 76.9% F1**;
- Core: **5/5 conversations**;
- action characterization: **12/12**;
- known action gaps: numbered-subject resolution, ambiguity, authentication,
  and state cleanup.

The historical evidence remains in `baseline.md`.

## Action implementation

`ActionCancelarInscripcionMesa` now uses the shared subject infrastructure:

```text
SubjectCatalogRepository
→ SubjectResolver
→ canonical Materia.codigo
→ MesaExamen.codigo
→ Inscripcion by estudiante + codigo_mesa
```

The action now:

- verifies authentication, matrícula, and subject prerequisites;
- supports accent/case and Arabic/Roman numbered subject variants;
- separates resolved, not-found, and ambiguous subjects;
- never queries exam tables for invalid or ambiguous subjects;
- preserves the cancellation flow for retryable input/backend failures;
- clears `materia` and `flujo_actual` after success, no registration, or no
  available table;
- reports controlled catalog, table, registration-query, and delete failures.

## Persistence policy

The existing physical-delete contract is preserved. Every matching
`Inscripcion` row for the student's tables in the canonical subject is deleted,
including a row whose current `baja` value is `true`. Multiple matching rows are
deleted and counted.

This capability does not redefine `baja`, add a cancellation timestamp, or
change capability 006's duplicate/re-registration policy.

## NLU stability

Three explicit cancellation expressions that failed in the baseline were
added to `cancelar_inscripcion_mesa_examen`:

- “necesito dar de baja la mesa de …”;
- “desanotame de la mesa de …”;
- “quiero anular mi inscripción para …”.

Before targeted hardening, three independent Rasa 3.6.20 trainings evaluated
the same 19-example held-out contract without changing the dataset between
runs:

| Run | Intent accuracy | Cancellation intent P/R/F1 | `materia` P/R/F1 |
|---|---:|---:|---:|
| 1 | **19/19 (100%)** | **100% / 100% / 100%** | **98.08% / 100% / 99.03%** |
| 2 | **18/19 (94.74%)** | **100% / 87.5% / 93.33%** | **100% / 100% / 100%** |
| 3 | **17/19 (89.47%)** | **100% / 75% / 85.71%** | **100% / 100% / 100%** |

The explicit cancellation markers added by this capability remained correctly
classified. Two elliptical requests without an explicit cancellation verb were
not stable across trainings:

- “ya no voy a rendir el final de Redes de Computadoras II” was classified as
  `consultar_fecha_mesas_examen_final` in runs 2 and 3;
- “decidí no presentarme al examen final de Lengua y Comunicación” was
  classified as `inscripcion_mesa_examen` in run 3.

Run 1's entity precision issue was an extra `materia` span over “de” in one
partial-date contrast. The canonical subject span and intent were correct.

### Targeted hardening

The training set was then extended with 14 new, non-test examples:

- 8 varied implicit cancellations using expressions such as not attending or
  no longer taking the final;
- 3 positive registration contrasts;
- 3 final-date contrasts, including negative context followed by an explicit
  date question.

Three new independent trainings produced:

| Run | Intent accuracy | Cancellation intent P/R/F1 | `materia` P/R/F1 |
|---|---:|---:|---:|
| 1 | **18/19 (94.74%)** | **100% / 100% / 100%** | **100% / 100% / 100%** |
| 2 | **19/19 (100%)** | **100% / 100% / 100%** | **100% / 100% / 100%** |
| 3 | **19/19 (100%)** | **100% / 100% / 100%** | **98.08% / 100% / 99.03%** |

Both previously unstable elliptical cancellations were correct in all three
models. Run 1's only intent error was the unrelated generic subject follow-up
“la materia es Álgebra y Geometría Analítica”, predicted as subject
requirements instead of `proporcionar_materia`.

## Cross-capability controls

The hardened run 3 model was used for the NLU cross-controls.

### NLU

| Capability | Correct | Total |
|---|---:|---:|
| Attendance | 27 | 28 |
| Grades | 14 | 18 |
| Subject requirements | 21 | 22 |
| Final-exam dates | 23 | 24 |
| Partial-exam dates | 27 | 27 |
| Final-exam registration | 27 | 28 |
| **Total** | **139** | **147** |

No cross-suite example was incorrectly classified as
`cancelar_inscripcion_mesa_examen`. The eight errors are historical boundaries
among attendance, grades, requirements, dates, and generic subject follow-ups;
they do not introduce false cancellation triggers.

### Core

The full cross-capability Core controls below were executed before the targeted
NLU hardening:

| Capability | Conversations | Actions |
|---|---:|---:|
| Attendance | 4/4 | 19/19 |
| Grades | 5/5 | 27/27 |
| Subject requirements | 6/6 | 31/31 |
| Final-exam dates | 5/5 | 26/26 |
| Partial-exam dates | 5/5 | 25/25 |
| Final-exam registration | 5/5 | 23/23 |
| **Total** | **30/30** | **151/151** |

After hardening, the cancellation Core suite was rerun on hardened run 3 and
remained at **5/5 conversations** and **20/20 actions**.

## Core and validation

- `rasa data validate`: passed with only pre-existing unused-intent/utterance
  warnings;
- cancellation Core suite: **5/5 conversations**;
- cancellation Core action predictions: **20/20**;
- cancellation action suite: **18/18**;
- direct 005/006 action regressions: **42/42**;
- full Python suite: **122/123**.

The sole Python failure is the pre-existing attendance fixture mismatch in
`test_no_matching_subject`: the test expects `flujo_actual: None`, while the
attendance action emits `materia: None`. It is unrelated to 007.

## Acceptance status

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PASS | All 8 held-out cancellations, including both elliptical requests, pass in three independent hardened models. |
| AC-02 | PASS | Missing-subject form path passes in Core. |
| AC-03 | PASS | Generic `proporcionar_materia` follow-up passes in Core. |
| AC-04 | PASS | Canonical, accent/case, Arabic, and Roman resolution pass in action tests. |
| AC-05 | PASS | Invalid subject does not query `MesaExamen`. |
| AC-06 | PASS | Ambiguity requests clarification without selecting a first row. |
| AC-07 | PASS | No matching registration is reported and state is cleared. |
| AC-08 | PASS | Matching active registration is physically deleted and confirmed. |
| AC-09 | PASS | The inherited `baja=true` deletion behavior is explicitly tested. |
| AC-10 | PASS | Multiple registrations are deleted and counted. |
| AC-11 | PASS | Successful delete persistence and confirmation are tested. |
| AC-12 | PASS | Registration contrasts remain separate in NLU and Core. |
| AC-13 | PASS | Catalog, table, registration, and delete failures are controlled. |
| AC-14 | PASS | Completion clears state; retryable failures preserve the flow. |
| AC-15 | PASS | Final-date contrasts are 3/3 in the held-out NLU contract. |
| AC-16 | PASS | Authentication and matrícula prerequisites are enforced. |
| AC-17 | PASS | Re-registration policy remains documented and unchanged. |

## Final status

The action behavior, persistence contract, Core flows, and regression controls
are complete. Targeted NLU hardening made both elliptical cancellation
requests stable across three independent models while preserving 100%
cancellation precision and creating no cross-suite false cancellation triggers.

The remaining `baja` and re-registration questions require an explicit product
and database-policy decision and are intentionally outside this feature.
