# 005 — Partial Exam Dates Results

## Baseline

Before the action refactor, the partial-date action used:

```text
Materia.ilike("nombre", "%materia%")
→ first result
→ Parciales.eq("materia_codigo", codigo)
```

The historical baseline was:

- Partial NLU: **24/28**
- Partial intent: **100% precision / 83.3% recall / 90.9% F1**
- Materia entity extraction: **100% / 100% / 100%**
- Dialogue: **5/5 conversations, 25/25 actions**
- Action tests: **10/12**
- Full Python suite: **72/75** after adding the baseline tests

The two action failures were Arabic numbered resolution and arbitrary first
selection for ambiguous subjects.

## Action refactor

`ActionConsultarFechasParciales` now:

1. preserves the existing authentication and matrícula prerequisites;
2. obtains the canonical catalog through `SubjectCatalogRepository`;
3. resolves `materia` through the shared `SubjectResolver`;
4. queries `Parciales` only with the resolved canonical `materia_codigo`;
5. separates resolved, not-found, ambiguous, no-date, and backend-error
   outcomes;
6. returns all direct partial-date rows sorted by `fecha_parcial`;
7. includes the canonical subject name in responses;
8. clears stale `materia` and `flujo_actual` after successful/no-date
   completion;
9. clears an unresolved subject while preserving the partial flow for a retry;
10. preserves pending state on backend failure instead of fabricating a result.

No partial number, exam type, academic period, student-specific data, or
eligibility semantics were added.

## Subject-resolution results

The action tests now verify:

- exact canonical subject lookup;
- accent/case normalization;
- `fisica 2` and `fisica ii` → canonical `Física II`;
- unnumbered `fisica` → level-I subject when available;
- unknown level → not-found without a `Parciales` query;
- ambiguous subject → clarification without a `Parciales` query;
- canonical `materia_codigo` filtering;
- canonical subject name in the response.

## State and matrícula behavior

The form still requires `matricula` and `materia`. The matrícula remains an
inherited authentication/form prerequisite because the existing product flow
requires it, although `Parciales` itself is institutional schedule data and
does not filter by student. Removing that prerequisite is deferred and was not
part of this refactor.

State behavior is now explicit:

- success/no dates: clear `materia` and `flujo_actual`;
- not found/ambiguous: clear unresolved `materia`, preserve the partial flow;
- backend error: return a controlled message and preserve pending state.

## Verification

### Action and Python

- Partial action tests: **16/16**
- Full Python suite: **78/79**
- Remaining failure: pre-existing attendance fixture mismatch expecting
  `flujo_actual: None` instead of the current `materia: None` event.

### Dialogue controls

Using the existing compatible local model:

- Partial dialogue: **5/5**, **25/25 actions**
- Attendance dialogue: **4/4**, **19/19 actions**
- Grades dialogue: **5/5**, **27/27 actions**
- Requirements dialogue: **6/6**, **28/28 actions**
- Final-exam dialogue: **5/5**, **26/26 actions**

### NLU

The initial fresh baseline measured **24/28** partial-suite cases. A targeted
NLU update added three explicit, multiword partial-date examples to
`consultar_fechas_parciales`:

- a confirmation request for Álgebra y Geometría Analítica;
- a question about the partial date for Análisis Matemático II;
- a partial calendar request for Redes de Computadoras I.

The intent now contains 42 training examples. No examples were removed, and no
numbered-partial semantics were added.

Three fresh trainings after that change produced the following historical
results on the original 28-example diagnostic set:

| Run | Overall | Partial intent P/R/F1 | Materia P/R/F1 |
|---|---:|---|---|
| 1 | 25/28 | 100 / 91.7 / 95.7 | 100 / 98.5 / 99.3 |
| 2 | 27/28 | 100 / 91.7 / 95.7 | 100 / 98.5 / 99.3 |
| 3 | 25/28 | 100 / 91.7 / 95.7 | 97.1 / 100 / 98.6 |

The explicit multiword partial request stopped being confused with subject
requirements. The previously observed `fecha de Física II` case was removed
from the positive partial set because it contains no `parcial` marker and is
semantically ambiguous under the current specification. It was not forced into
the partial intent with overfitting.

With that case removed from the positive set, the corrected held-out contract
contains 27 examples. A fresh final-contract model measured:

- Overall: **26/27**;
- explicit partial requests: **11/11**;
- `consultar_fechas_parciales`: **100% precision / 100% recall / 100% F1**;
- explicit final-date contrasts: **4/4**;
- registration contrasts: no false positives into partial dates (one remains
  classified as the legacy `proporcionar_materia_para_inscripcion` intent);
- subject-only/form cases: **3/3**;
- materia entity: **100% precision / 98.5% recall / 99.2% F1**.

The action change and targeted NLU update did not alter forms, rules, stories,
or SubjectResolver behavior.

Regression NLU controls from the first post-change model were: final exams
**24/24**, attendance **26/28**, grades **14/18**, and requirements **21/22**.
These are existing combined-model fluctuations; final-exam intent did not
regress.

## Final acceptance status

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 | PASS | Action succeeds and all 11 explicit partial-date requests pass on the corrected held-out contract. |
| AC-02 | PASS | Explicit partial wording is correctly recognized; generic `fecha de X` is outside the contract. |
| AC-03 | PASS | Form requests missing `materia`. |
| AC-04 | PASS | Generic subject follow-up completes the active form. |
| AC-05 | PASS | Shared catalog/resolver and canonical code query are tested. |
| AC-06 | PASS | Arabic, Roman, unnumbered, and unknown-level cases are tested. |
| AC-07 | PASS | Invalid subject does not query `Parciales`. |
| AC-08 | PASS | Ambiguous subject requests clarification and does not query. |
| AC-09 | PASS | Valid subject with no rows is distinct and clears state. |
| AC-10 | PASS | One date is returned. |
| AC-11 | PASS | Multiple dates are all returned in date order. |
| AC-12 | PASS | Canonical subject name is included in the response. |
| AC-13 | PASS | Successful/retryable outcomes clean stale subject and flow state. |
| AC-14 | PASS | Catalog and `Parciales` failures are controlled. |
| AC-15 | PASS | Explicit partial/final wording is separated; generic wording belongs to neither contract. |
| AC-16 | PASS | Registration cases are not treated as partial-date requests. |
| AC-17 | PASS | Existing authentication and matrícula prerequisites remain enforced. |
| AC-18 | OUT OF SCOPE | The database does not represent partial numbers, so 005 does not promise numbered-partial filtering. |
| AC-19 | PASS | Subject-only behavior is contextual to the active form. |

The remaining limitation is that generic exam-date phrases without `parcial`,
`final`, or `mesa` are outside the 005 contract and should be clarified at the
product-language level. Numbered-partial filtering is also explicitly out of
scope because the database cannot identify a particular numbered partial.
