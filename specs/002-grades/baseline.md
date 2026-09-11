# Grades Capability — Pre-Change Baseline

## Purpose

This document records the measured behavior of the grades capability before
any production implementation changes. It is historical characterization
evidence and must not be rewritten after later improvements.

## NLU baseline

The held-out dataset was `tests/nlu_grades_test.yml` (23 examples).

- Overall accuracy: **10/23 (43.5%)**.
- `consultar_notas`: precision **100.0%**, recall **33.3%**, F1 **50.0%**.
- `materia`: precision **78.6%**, recall **95.7%**, F1 **86.3%**.

Notable errors included subject-bearing grade requests classified as
`consultar_asistencia` or `proporcionar_materia`, generic grade language
classified as attendance or unrelated intents, and contrastive requests about
exam dates, requirements, or subjects classified as attendance. Short
subject-only inputs were commonly classified as a subject-provision intent.

The dataset covers generic personal-grade language, subject-bearing requests,
accent/case and Arabic/Roman variants, short phrasing, and contrastive intents.

## Dialogue baseline

The characterization stories are in `tests/test_grades_stories.yml`.

- Conversations passed: **5/5 (100%)**.
- Action accuracy: **24/24 (100%)**.
- Scenarios cover subject-present requests, missing subject, subject follow-up,
  repeated subject replacement, and invalid-subject handling.

## Action baseline

The unit tests are in `tests/test_action_consultar_notas.py`.

The current behavior under test includes:

- authentication and matrícula prerequisites;
- integer matrícula validation;
- broad student-grade lookup;
- substring filtering by `Materia.nombre`;
- multiple grade records;
- no-grade response;
- invalid-subject response when other grades exist;
- backend error handling;
- output of `nota`, `descripcion`, and `created_at`.

Specification characterization tests intentionally expose behavior that is not
implemented yet:

- canonical `materia_codigo` filtering;
- shared subject resolver usage;
- ambiguity handling without arbitrary selection.

The grades action characterization suite ran **10/12** tests successfully. The
two failing tests are intentional specification probes: canonical numbered
subject resolution is not applied, and an ambiguous subject still causes the
broad `Notas` query instead of stopping for clarification.

## AC baseline

| Criterion | Baseline status | Evidence / reason |
|---|---|---|
| AC-01 | PARTIAL | Form/action path exists, but canonical subject handling is absent. |
| AC-02 | FAIL | Held-out grades NLU recall was 33.3%; several personal-grade phrasings were misclassified. |
| AC-03 | PASS | The missing-subject characterization story passed and the form requests `materia`. |
| AC-04 | PASS | The subject-follow-up characterization story passed and reached `action_consultar_notas`. |
| AC-05 | FAIL | `ActionConsultarNotas` does not use `SubjectCatalogRepository` or `SubjectResolver`. |
| AC-06 | FAIL | Arabic/Roman and unnumbered-to-level-I resolution is not used by the action. |
| AC-07 | PARTIAL | An invalid-subject story passes, but detection occurs only after broad student-grade retrieval. |
| AC-08 | FAIL | No ambiguity detection exists in the grades action. |
| AC-09 | PASS | The valid-subject/no-grade characterization test passes with a specific no-grades response. |
| AC-10 | PARTIAL | Multiple records are returned, but substring matching can select unintended records. |
| AC-11 | PARTIAL | Backend fields are displayed, alongside legacy `/10` and color formatting. |
| AC-12 | PARTIAL | The repeated-query story passes, but dedicated stale-slot/action coverage is incomplete. |
| AC-13 | PASS | Backend exceptions produce a controlled user-facing error. |
| AC-14 | PARTIAL | Authentication/matrícula remain external, but broad lookup and legacy presentation remain. |

## Known implementation gaps

- Subject resolution uses lowercase substring matching instead of canonical
  catalog resolution.
- The action queries all grades for a student before filtering by subject.
- Invalid subject and no-grades outcomes can be conflated when the student has
  no grade rows.
- Ambiguous subject expressions are not detected.
- The grades action does not constrain the query by canonical
  `Notas.materia_codigo`.
- Repeated subject replacement is not covered by an independent action or
  dialogue regression test.
- No dedicated grades NLU held-out dataset existed before this baseline.

## Regression controls

Attendance controls and the existing Core suite are recorded separately from
the grades baseline. Their fresh results are reported with the execution
results for this baseline and are not used to reinterpret the historical
attendance baseline.

Fresh controls for this baseline were:

- Attendance held-out NLU: **28/28 intent cases**, with `consultar_asistencia`
  19/19 and policy 9/9; the `materia` report was 21/22 precision and 146/147
  recall (F1 approximately **99.7%**).
- Attendance dialogue: **4/4 conversations**, **19/19 actions**.
- Existing Core suite (`tests/test_stories.yml`): **4/8 conversations** and
  **26/34 actions (76.5% action accuracy)**, matching the current legacy
  control behavior.
- Full Python unit suite: **33/35 passing**. The two failures are the
  intentional grades specification probes described above; no production code
  was changed to make them pass.

## Recommended first implementation step

Add characterization-backed subject resolution to the grades action using the
existing authoritative catalog and resolver, while preserving the current
authentication, matrícula, and grade-record semantics. The first production
gap to address is replacing the broad student query plus substring filtering
with canonical subject resolution and a canonical `materia_codigo` constraint.
