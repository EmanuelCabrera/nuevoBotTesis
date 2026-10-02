# 005 — Partial Exam Dates — Pre-Refactor Baseline

This document records the measured behavior of the partial-exam-date
capability before production refactoring. It is historical evidence and must
not be rewritten after implementation changes.

## Test environment

- Python 3.9.12
- Rasa 3.6.20
- rasa-sdk 3.6.2
- spaCy 3.7.2
- DIETClassifier: 75 epochs
- Fresh model: `.tmp_005_baseline/model/partial_baseline.tar.gz`

## NLU baseline

Dataset: `tests/nlu_partial_exam_dates_test.yml`.

- Overall: **24/28 (85.7%)**
- `consultar_fechas_parciales`: precision **100%**, recall **83.3%**, F1
  **90.9%** (12 cases)
- `materia`: precision **100%**, recall **100%**, F1 **100%** (68 annotated
  spans)
- Subject-only contextual cases: **3/3** as `proporcionar_materia`
- Final-date contrast cases: **4/4** remained final-date requests, although
  one underspecified “fecha de Física II” partial case was classified as final.
- Registration contrast cases: no case was classified as partial; one was
  classified as the legacy `proporcionar_materia_para_inscripcion` intent.

### Exact partial-suite failures

| Input | Expected | Predicted | Confidence |
|---|---|---|---:|
| `necesito revisar la fecha del parcial de Álgebra y Geometría Analítica` | `consultar_fechas_parciales` | `consultar_requerimientos_materia` | 60.7% |
| `fecha de Física II` | `consultar_fechas_parciales` | `consultar_fecha_mesas_examen_final` | 100.0% |

The first is a partial-versus-requirements boundary error. The second is
intentionally underspecified language: it has no word indicating partials and
therefore exposes a product-language ambiguity rather than a reliable partial
date contract.

## Dialogue baseline

Suite: `tests/test_partial_exam_dates_stories.yml`.

- Conversations: **5/5**
- Action predictions: **25/25**

Passing scenarios:

- explicit request with subject;
- request without subject activates `fechas_parciales_form`;
- generic `proporcionar_materia` fills the active form;
- matrícula is collected before the subject when both are missing;
- a later explicit request supplies a different subject.

These are tracker-state characterization stories. They provide form coverage,
but they do not prove that isolated production NLU will always classify every
subject-only reply correctly.

## Action baseline

Suite: `tests/test_action_consultar_fechas_parciales.py`.

- Passing: **10/12**
- Failing: **2/12**

### Observed current behavior

Passing behavior includes authentication and matrícula prerequisites, missing
slot flow preservation, exact `ILIKE` lookup, one and multiple date responses,
date ordering, invalid-subject handling, controlled catalog/partial backend
errors, and successful `materia`/`flujo_actual` cleanup.

Expected contract failures:

1. `fisica 2` is sent to `Materia.ilike` and does not resolve through the
   shared catalog to canonical `Física II`.
2. An ambiguous expression such as `Física` selects the first `ILIKE` result
   and queries `Parciales` instead of asking for clarification.

Additional data-quality concern: the no-results and invalid-subject branches
clear only `flujo_actual`, leaving the current `materia` value in state.

## Acceptance baseline

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PARTIAL | Exact action flow works, but NLU partial recall is 10/12. |
| AC-02 | PARTIAL | `consultar_fechas_parciales` recall is 83.3%; one partial phrase is confused with final dates. |
| AC-03 | PASS | Dialogue activates `fechas_parciales_form` and requests `materia`. |
| AC-04 | PASS | Generic `proporcionar_materia` completes the active form in Core characterization. |
| AC-05 | FAIL | Action uses `Materia.ilike` instead of `SubjectCatalogRepository`/`SubjectResolver`. |
| AC-06 | FAIL | `fisica 2` does not resolve to canonical `Física II`. |
| AC-07 | PASS | Invalid subject is reported before querying `Parciales`. |
| AC-08 | FAIL | Ambiguous subject selects an arbitrary first match. |
| AC-09 | PARTIAL | Zero rows are distinguished from subject-not-found, but the response is not canonical-subject-specific and stale `materia` remains. |
| AC-10 | PASS | One stored date is returned. |
| AC-11 | PASS | All stored rows are returned in `fecha_parcial` order. |
| AC-12 | FAIL | Current response does not identify the canonical subject name. |
| AC-13 | PARTIAL | Success clears state and Core replacement passes, but no-result branches retain `materia`. |
| AC-14 | PASS | Catalog and partial backend exceptions produce controlled errors. |
| AC-15 | PARTIAL | Explicit partial cases mostly separate from finals, but underspecified “fecha de Física II” is inherently ambiguous. |
| AC-16 | PASS | Registration contrast cases do not become partial-date requests. |
| AC-17 | PASS | Authentication and matrícula prerequisites are enforced by the current action/form flow. |
| AC-18 | NOT MEASURED | The database has no partial-number field; no dedicated test verifies ordinal semantics are not inferred. |
| AC-19 | PASS | Subject-only examples are classified as `proporcionar_materia` and active-form continuation passes. |

## Current implementation gaps

- `Materia.ilike(...).first()` is used for subject identity;
- no shared canonical resolver or ambiguity outcome;
- Arabic/Roman numbering is not supported by the action;
- valid-subject/no-partials is a generic response without canonical subject
  context;
- invalid/no-result branches leave stale `materia` state;
- partial-number language cannot be backed by the current schema;
- no dedicated production acceptance test existed before this baseline;
- generic wording such as “fecha de Física II” is ambiguous between partial
  and final dates.

## Regression controls

Using the same fresh model:

- Attendance NLU: **26/28**; dialogue **4/4**, **19/19 actions**.
- Grades NLU: **15/18**; dialogue **5/5**, **27/27 actions**.
- Requirements NLU: **21/22**; dialogue **6/6**, **28/28 actions**.
- Full Python suite after adding these baseline tests: **72/75**. The three
  failures are the two intentional partial-action characterization failures
  plus the pre-existing attendance fixture mismatch expecting `flujo_actual:
  None` instead of the current `materia: None` event.

These fluctuations are baseline evidence, not production changes.

## Recommended next refactor

1. Preserve the form and inherited authentication/matrícula prerequisites.
2. Refactor the action to obtain the canonical catalog and use
   `SubjectResolver`.
3. Query `Parciales` by canonical `materia_codigo`.
4. Separate resolved, not-found, ambiguous, no-results, and backend-error
   outcomes, including state cleanup.
5. Re-run the action and dialogue tests before considering any NLU boundary
   improvement.

No specialized `proporcionar_materia_para_parciales` intent exists in the
current repository; generic `proporcionar_materia` is sufficient while the
form is active.
