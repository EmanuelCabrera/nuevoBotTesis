# 003-subject-requirements — Pre-change Baseline

This document records measured behavior before changing the subject-requirements implementation. These historical values must not be reinterpreted as accepted behavior.

## NLU baseline

Dataset: `tests/nlu_subject_requirements_test.yml`.

- Overall accuracy: **18/22 (81.8%)**.
- `consultar_requerimientos_materia`: precision **100%**, recall **75%**, F1 **85.7%** (12 cases).
- `materia` entity: precision **95.5%**, recall **100%**, F1 **97.7%** (42 entities).

### Observed confusions

- One requirements case was classified as `proporcionar_materia_para_requerimientos`.
- One requirements case was classified as `proporcionar_materia`.
- One partial-exam-date case was classified as `consultar_fecha_mesas_examen_final`.

## Dialogue baseline

Suite: `tests/test_subject_requirements_stories.yml`.

- Conversations correct: **5/6 (83.3%)**.
- Actions correct: **21/22 (95.5%)**.

The contextual subject-follow-up scenario failed:

```text
consultar_requerimientos_materia
→ request subject
→ proporcionar_materia_para_requerimientos
→ action_default_fallback
```

The requirements action did not execute. The ambiguity story is present, but its prediction does not yet demonstrate the clarification behavior required by the specification.

## Action baseline

Suite: `tests/test_action_consultar_requerimientos_materia.py`.

- Passing: **10/12**.
- Failing: **2/12**.

Passing behavior included authentication, matrícula and subject prerequisites; flow preservation when data is missing; successful one- and multi-requirement queries; valid subject with no requirements; invalid-subject distinction; controlled backend errors; successful state cleanup; and canonical names present in the fixture response.

Failing behavior:

1. `fisica 2` was not resolved to canonical `Física II` / `FIS2` because the legacy `ILIKE` lookup does not match `Física II`.
2. An ambiguous expression selected the first match and queried `MateriaEquivalencia` instead of requesting clarification.

The complete Python suite finished at **45/47**, with the same two failures.

## Acceptance baseline

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PASS | Explicit scenario executed the action. |
| AC-02 | PARTIAL | Requirements/correlative examples exist, but NLU recall was 75%. |
| AC-03 | PASS | Action asks for the subject and preserves `flujo_actual`. |
| AC-04 | FAIL | Contextual follow-up ended in `action_default_fallback`. |
| AC-05 | FAIL | Shared canonical resolution is not used. |
| AC-06 | FAIL | `fisica 2` did not resolve to the canonical numbered subject. |
| AC-07 | PASS | Unknown subject produced a distinct message. |
| AC-08 | FAIL | First result was selected for an ambiguous expression. |
| AC-09 | PASS | Valid subject with no rows produced a no-requirements message. |
| AC-10 | PASS | Both direct Física II relationships were returned by the fixture. |
| AC-11 | PARTIAL | Related names are shown, but canonical queried-subject identity is not guaranteed. |
| AC-12 | PASS | Successful action clears `materia` and `flujo_actual`; a robust end-to-end replacement test is still missing. |
| AC-13 | PARTIAL | A controlled message exists, but post-exception flow state is not guaranteed. |
| AC-14 | NOT MEASURED | No dedicated administrative-requirements suite exists. |
| AC-15 | NOT MEASURED | No dedicated academic-equivalences suite exists. |
| AC-16 | PARTIAL | The query is direct, but no real transitive-expansion guard test exists. |

## Known implementation gaps

- partial `ILIKE` subject lookup;
- first-result selection;
- no shared `SubjectCatalogRepository`/`SubjectResolver` integration;
- no accent, case, or numbering normalization in this action;
- no ambiguity handling;
- follow-up depends on a specialized intent without an explicit intent-specific rule;
- inconsistent state after backend exceptions;
- no dedicated requirements unit, NLU, or integration tests before this characterization.

## Regression controls

### Grades

- NLU `tests/nlu_grades_test.yml`: **8/9 (88.9%)** in the model trained for this baseline.
- `consultar_notas`: precision, recall and F1 **100%** on the two control cases.
- Dialogue `tests/test_grades_stories.yml`: **5/5**.

### Attendance

- NLU `tests/nlu_attendance_test.yml`: **28/28**.
- `consultar_asistencia`: **19/19**.
- `informar_asistencia`: **9/9**.
- Dialogue `tests/test_attendance_stories.yml`: **4/4**.

No current general Core suite file exists in the repository.

## Recommended next step

Integrate canonical subject resolution into the requirements action using the shared components, keeping `resolved`, `not_found`, and `ambiguous` outcomes separate.

Before or during that implementation, audit and clean `proporcionar_materia_para_requerimientos`: its examples mix complete requirements requests with contextual subject replies, and the flow should align with the contextual pattern already used by attendance and grades.
