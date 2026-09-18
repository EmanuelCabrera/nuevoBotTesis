# 004 — Final Exam Dates — Pre-Change Baseline

## Purpose

This document records the measured behavior of the final-exam-date capability before production refactoring. These results are historical evidence and must not be rewritten after implementation changes.

## Test environment

- Python 3.9.12
- Rasa 3.6.20
- rasa-sdk 3.6.2
- spaCy 3.7.2
- Fresh model: `models/final_exam_dates_baseline.tar.gz`

## NLU baseline

Dataset: `tests/nlu_final_exam_dates_test.yml`.

- Overall: **20/24 (83.3%)**
- `consultar_fecha_mesas_examen_final`: precision **90.9%**, recall **83.3%**, F1 **87.0%** (12 cases)
- `materia`: precision **97.7%**, recall **95.6%**, F1 **96.6%**
- Partial-date contrastive cases: **4/4**
- Registration contrastive cases: **2/4**
- Contextual subject-only cases expected as `proporcionar_materia`: **4/4**

### Exact NLU failures

| Input | Expected | Predicted | Confidence |
|---|---|---|---:|
| `qué día es la mesa de Física II` | `consultar_fecha_mesas_examen_final` | `proporcionar_materia_para_mesas` | 56.4% |
| `calendario de mesas para Análisis Matemático II` | `consultar_fecha_mesas_examen_final` | `proporcionar_materia_para_mesas` | 54.6% |
| `anotame al final de Física` | `inscribirse_mesa_examen` | `consultar_fecha_mesas_examen_final` | 64.7% |
| `quiero reservar lugar en la mesa de Álgebra` | `inscribirse_mesa_examen` | `proporcionar_materia_para_mesas` | 65.7% |

No dedicated final-date case was confused with `consultar_fechas_parciales`. The observed boundary weakness is primarily the specialized mesa intent and the date-versus-registration distinction.

## Dialogue baseline

Suite: `tests/test_final_exam_dates_stories.yml`.

- Conversations: **5/5**
- Actions: **26/26**
- Conversation accuracy: **100%**
- Action accuracy: **100%**

Passing scenarios:

- request with subject already present;
- missing-subject collection;
- current specialized subject follow-up;
- generic `proporcionar_materia` follow-up while the form is active;
- repeated query with subject replacement.

The Core tests receive intents directly and therefore do not demonstrate that isolated NLU will choose the correct follow-up intent.

## Action baseline

Suite: `tests/test_action_consultar_mesas_examen.py`.

- Passing: **9/11**
- Failing: **2/11**

Passing behavior:

- authentication prerequisite;
- exact valid-subject lookup;
- invalid-subject handling;
- valid subject with no mesas;
- one mesa response;
- multiple mesa response;
- canonical name when the exact catalog row is selected;
- controlled backend error;
- successful `materia` cleanup.

Failing behavior:

1. `fisica 2` does not resolve to canonical `Física II`; the partial `ILIKE` lookup returns no subject.
2. An ambiguous expression selects the first partial match and queries `MesaExamen` instead of requesting clarification.

The complete Python suite finished at **56/58**, with the same two expected failures.

## Specialized-intent baseline

`proporcionar_materia_para_mesas` contains 18 examples. They are not plain subject-only replies: they mix contextual wording with complete mesa requests such as “Quiero ver las mesas de Física” and “Mesas de Historia”.

Measured effects:

- two explicit final-date cases were classified as `proporcionar_materia_para_mesas`;
- one registration case was classified as `proporcionar_materia_para_mesas`;
- all four genuinely subject-only held-out cases were correctly classified as generic `proporcionar_materia`.

The current form can continue with generic `proporcionar_materia` through active-loop context, so the specialized intent appears redundant, but it is preserved during this baseline step.

## Acceptance baseline

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PARTIAL | Core flow passes, but two explicit final-date NLU cases select the specialized mesa intent. |
| AC-02 | PARTIAL | Final/mesa recall is 83.3%. |
| AC-03 | PASS | Missing-subject dialogue activates `consultar_mesas_form` and requests `materia`. |
| AC-04 | PASS | Both specialized and generic subject follow-up stories complete the active form. |
| AC-05 | FAIL | The action does not use the shared catalog/resolver contract. |
| AC-06 | FAIL | `fisica 2` does not resolve to `Física II`. |
| AC-07 | PASS | Invalid subject is reported before querying mesas. |
| AC-08 | FAIL | Ambiguous subject selects the first `ILIKE` match. |
| AC-09 | PASS | Valid subject with no rows has a distinct no-mesas response. |
| AC-10 | PASS | One-mesa test returns code and date. |
| AC-11 | PASS | Multiple-mesa test returns every code and date. |
| AC-12 | PARTIAL | Exact lookup displays the catalog name, but canonical resolution is not guaranteed. |
| AC-13 | PASS | Successful action cleanup and repeated-query Core flow pass. |
| AC-14 | PASS | Backend exception produces a controlled error without fabricated data. |
| AC-15 | PASS | All explicit partial cases remain outside the final-date intent. |
| AC-16 | FAIL | Two of four registration contrasts fail, including one false positive into final dates. |
| AC-17 | PASS | Subject-only NLU is 4/4 as generic `proporcionar_materia`; active-form continuation passes. |
| AC-18 | PASS | Unauthenticated action execution is rejected without database access. |

## Subject-resolution gaps

- direct `Materia.nombre ILIKE` lookup;
- arbitrary first-result selection;
- no `SubjectCatalogRepository` reuse;
- no `SubjectResolver` reuse;
- no Arabic/Roman numbering equivalence;
- no explicit ambiguity result;
- canonical identity is reliable only when the raw expression already matches the selected row.

## Semantic-boundary gaps

- `proporcionar_materia_para_mesas` overlaps explicit final-date requests;
- registration language involving “mesa” or “final” is not reliably separated from date consultation;
- generic “exam date” wording remains a product-language ambiguity and is not asserted as final or partial in this baseline.

## Regression controls

### Attendance

- NLU: **28/28**
- `consultar_asistencia`: **19/19**
- `informar_asistencia`: **9/9**
- Dialogue: **4/4**, 19/19 actions

### Grades

- NLU mixed dataset: **18/18**
- Explicit grades: **10/10**
- Dialogue: **5/5**, 24/24 actions

### Subject requirements

- NLU mixed dataset: **21/22**
- Explicit requirements: **12/12**
- Dialogue: **6/6**, 28/28 predicted actions in the current suite

The remaining requirements-control failure is an unrelated partial-versus-final exam-date boundary:

```text
cuál es la fecha del examen de Redes de Computadoras I
expected: consultar_fechas_parciales
predicted: consultar_fecha_mesas_examen_final
```

## Recommended first production refactor

Integrate `SubjectCatalogRepository` and `SubjectResolver` into `action_consultar_mesas_examen`, preserving distinct resolved, not-found, ambiguous, and valid-without-mesas outcomes. After action behavior is characterized and corrected, audit and remove `proporcionar_materia_para_mesas` in favor of explicit `consultar_fecha_mesas_examen_final` requests plus generic `proporcionar_materia` under active form context.
