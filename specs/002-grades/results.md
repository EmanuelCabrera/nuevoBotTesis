# 002-grades Results

## Baseline

The historical pre-change baseline is preserved in `baseline.md`:

- Grades NLU: 10/23 (43.5%). `consultar_notas` recall was 33.3% (F1 50.0%).
- Grades action characterization: 10/12; canonical resolution and ambiguity
  were the two intentional specification failures.
- Grades dialogue: 5/5, but the action still used broad retrieval and
  substring subject matching.
- Main gaps were weak grades-language recognition, non-canonical subject
  lookup, arbitrary ambiguity handling, and lack of a canonical
  `materia_codigo` constraint.

## Implementation changes

The grades action now:

- reuses `SubjectCatalogRepository` and `SubjectResolver`;
- resolves expressions against the authoritative catalog and preserves the
  canonical `codigo` and `nombre`;
- queries `Notas` using `estudiante_id` plus canonical `materia_codigo`;
- separates resolved, not-found, ambiguous, and no-grades outcomes;
- does not query grades while a subject is ambiguous;
- preserves the existing `nota`, `descripcion`, `created_at`, and multiple
  grade-record behavior.

The grades follow-up flow now uses the same generic `proporcionar_materia`
intent already used by attendance. The former specialized
`proporcionar_materia_para_notas` intent was removed; explicit grade-request
examples were retained under `consultar_notas`, while subject-only replies
remain contextual to the active `notas_form`.

No authentication, matrícula, academic-period, schema, or unsupported grade
semantics were added.

## NLU improvements

The held-out contract was corrected so isolated subject-only replies are tested
in dialogue rather than treated as independent grades requests. Explicit grades
requests are evaluated separately from contrastive non-grades examples.

The pre-cleanup stability check had produced 10/10 explicit grades cases in
three runs. After removing the specialized follow-up intent and moving its
examples under `consultar_notas`, the fresh combined verification produced:

- Explicit grades requests: **9/10**.
- `consultar_notas`: precision **100%**, recall **90%**, F1 **94.7%** on the
  10 explicit grades cases.
- Contrastive cases incorrectly entering `consultar_notas`: **0/8**.
- The full 18-case mixed report had 15/18 correct because three contrastive
  examples were confused between other non-grades intents; none was a grades
  false positive.
- Grades `materia` entity report: precision **70.6%**, recall **92.3%**, F1
  **80.0%** (13 annotated entity cases). This remains an extraction-quality
  limitation outside the explicit intent score.

The targeted training change for the remaining explicit failure added a small
set of subject-bearing personal-result examples to `consultar_notas`. The
three-run stability check previously performed after that change returned
10/10 explicit grades cases and 100/100/100 `consultar_notas` precision,
recall, and F1 in each run.

## Final verification

### Test environment

Rasa was trained and evaluated with the existing Docker image
`nuevobottesis-rasa-server:latest` and the `personal_attendance_models` Docker
volume. The final model was trained with:

```text
docker run --rm --user 0 -v "$PWD:/app" -v personal_attendance_models:/out -w /app nuevobottesis-rasa-server:latest sh -lc 'rm -rf /out/grades_final && mkdir -p /out/grades_final && rasa train --force --fixed-model-name grades_final --out /out/grades_final'
```

The evaluation model was `/out/grades_final/grades_final.tar.gz`.

### Grades

- Held-out grades NLU: **15/18 overall**; **9/10 explicit grades**; zero
  false positives into `consultar_notas` among the 8 contrastive cases.
- `consultar_notas` explicit precision/recall/F1: **100%/90%/94.7%**.
- Grades dialogue: **5/5 conversations**, **24/24 actions**.
- Action tests: **12/12 passing**.

### Controls

- Full Python suite: **35/35 passing**.
- Attendance dialogue: **4/4 conversations**, **19/19 actions**.
- Attendance held-out NLU: **28/28**, including `consultar_asistencia` 19/19
  and `informar_asistencia` 9/9.
- Existing Core suite: **not executed** because the updated branch no longer
  contains `tests/test_stories.yml`; the file was removed by the attendance
  branch changes. This control therefore cannot be compared freshly here.

## Baseline comparison

| Area | Baseline | Final |
|---|---:|---:|
| Grades NLU overall | 10/23 (43.5%) | 15/18 mixed; 9/10 explicit |
| `consultar_notas` recall | 33.3% | 90% explicit |
| Grades action tests | 10/12 | 12/12 |
| Grades dialogue | 5/5 | 5/5 |
| Attendance NLU control | historical control | 28/28 fresh |
| Full Python suite | 33/35 | 35/35 |

## Acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 — Personal grades request with subject | PASS | Explicit NLU and grades story A (5/5 dialogue). |
| AC-02 — Personal grades language | PARTIAL | 9/10 explicit held-out requests; one explicit request was classified as `evaluacion_coneau`. |
| AC-03 — Missing subject | PASS | Grades story B verifies the form requests `materia`. |
| AC-04 — Subject follow-up | PASS | Grades story C verifies a subject-only reply continues to `action_consultar_notas`. |
| AC-05 — Canonical subject resolution | PASS | Action tests verify shared catalog/resolver use and canonical identity filtering. |
| AC-06 — Numbered subject variants | PASS | Action tests cover Arabic/Roman and unnumbered-to-level-I resolution. |
| AC-07 — Invalid subject | PASS | Invalid-subject unit/story coverage produces not-found without a grade query. |
| AC-08 — Ambiguous subject | PASS | Unit test verifies clarification behavior and no arbitrary grade query. |
| AC-09 — No grades | PASS | Valid canonical subject with zero records has a distinct no-grades response. |
| AC-10 — Multiple grades | PASS | Unit test returns multiple records individually. |
| AC-11 — Grade record consistency | PASS | Tests preserve `nota`, `descripcion`, and `created_at`; no invented academic meaning is required. |
| AC-12 — Subject replacement | PASS | Grades story D verifies a later subject replaces the earlier subject. |
| AC-13 — Backend failure | PASS | Backend-exception unit test verifies a controlled response without fabricated data. |
| AC-14 — Scope boundary | PASS | No auth/matrícula redesign, schema change, averages, pass/fail, period, or assessment-type semantics were introduced. |

## Out of scope / remaining debt

- Attendance policy-boundary instability is unrelated to 002-grades.
- The general Core regression control could not be rerun because
  `tests/test_stories.yml` is absent from the updated branch.
- Authentication and matrícula behavior remain prerequisites and were not
  redesigned.
- Academic-period filtering and assessment-type interpretation remain out of
  scope.
- No averages, pass/fail, promotion, or regularity semantics were added.
- Live Supabase integration is not covered by the mocked unit tests.
- The mixed grades NLU report still has two non-grades-to-non-grades
  misclassifications, and grades subject entity extraction is not perfect;
  neither is a false positive into `consultar_notas`.

## Conclusion

The grades follow-up simplification is functionally compatible with the
existing form and dialogue behavior: grades and attendance dialogue suites,
action tests, and the full Python suite pass. However, this post-cleanup NLU
run scored 9/10 on explicit grades requests, so `002-grades` should **not yet
be considered ready for final commit** until the remaining NLU regression is
resolved or accepted explicitly.
