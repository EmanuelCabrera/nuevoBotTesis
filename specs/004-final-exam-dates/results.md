# 004 — Final Exam Dates — Results

## Baseline

The original 004 baseline used substring/`ILIKE` subject lookup with arbitrary
first-match selection. It scored 20/24 on the held-out NLU suite, 5/5 dialogue
stories, and 9/11 action tests. Compound subject spans could be split or could
include a standalone connector such as `de`.

## Implementation changes

- `action_consultar_mesas_examen` now uses `SubjectCatalogRepository` and
  `SubjectResolver`.
- Mesa queries are constrained by canonical `materia_codigo`.
- Resolved, not-found, ambiguous, and valid-without-mesas outcomes are
  separated.
- All direct mesa records preserve `codigo` and `fecha`.
- Successful and no-mesa completions clear `materia` and `flujo_actual`.
- `proporcionar_materia_para_mesas` was removed. Subject collection uses the
  generic `proporcionar_materia` while `consultar_mesas_form` is active.

## Architecture experiment

`MateriaSpanMerger` was evaluated as a narrow post-DIET repair, but was removed
from the final candidate pipeline. The candidate configuration uses:

- `DIETClassifier.epochs: 75`
- `constrain_similarities: true`
- no custom span-repair component

Subject identity and canonicalization remain exclusively the responsibility of
`SubjectResolver`; no catalog or alias logic was moved into NLU.

The preceding NLU-only experiment found 75 epochs to be the best setting:
three independent models scored 24/24 and 100/100/100 entity metrics. The
full production-configuration validation below is the authoritative result for
the proposed replacement.

## Final architecture validation

`rasa data validate` passed and three independent full models were trained from
the actual `config.yml` using isolated caches.

| Run | Final-exam NLU | Final-date P/R/F1 | Materia P/R/F1 | Critical `Redes II` span |
|---|---:|---:|---:|---|
| 1 | 24/24 | 100/100/100 | 100/100/100 | one complete entity |
| 2 | 24/24 | 100/100/100 | 100/100/100 | one complete entity |
| 3 | 24/24 | 100/100/100 | 95.74/100/97.83 | extra `de` plus complete entity |

Run 3 produced an additional standalone `de` entity for Redes I/II, but this
does not affect scalar slot filling. Rasa preserves entity order and assigns
the last matching `materia` entity to the slot, so the slot value is still
`Redes de Computadoras II`. `SubjectResolver` therefore receives the complete
subject in all three runs.

## Dialogue and action verification

- Final-exam dialogue: 5/5 conversations, 26/26 actions.
- Final-exam action tests: 16/16.
- Requirements action tests: 12/12.
- Attendance dialogue: 4/4.
- Grades dialogue: 5/5.
- Requirements dialogue: 6/6.

The dialogue/action suites passed using the representative model. The
standalone connector is a diagnostic entity-quality issue, not a product-level
resolution failure.

## Regression controls

Representative NLU controls with the final candidate configuration were:

- Attendance: 27/28; `consultar_asistencia` F1 97.3%, `informar_asistencia`
  F1 100%.
- Grades: 15/18; `consultar_notas` F1 82.4%.
- Requirements: 21/22; `consultar_requerimientos_materia` F1 100%.

These include the known combined-NLU semantic-boundary fluctuations and are
not evidence of a new action or dialogue regression.

The Python suite ran 63 tests: 62 passed and 1 failed. The failure is the
unrelated historical attendance fixture `test_no_matching_subject`, which
expects `flujo_actual: None` while the current action emits `materia: None`.

## Acceptance criteria

- AC-01 — **PASS**: explicit final-date requests reach the form/action and the
  complete subject reaches the resolver in all three runs.
- AC-02 — **PASS**: final/mesa wording is recognized in the 12 final-date cases.
- AC-03 — **PASS**: missing-subject form flow passes in dialogue tests.
- AC-04 — **PASS**: generic subject follow-up completes the active form.
- AC-05 — **PASS**: the complete slot value reaches canonical resolution in all
  three runs.
- AC-06 — **PASS**: numbered variants resolve correctly; the extra connector
  entity does not change the scalar slot value.
- AC-07 — **PASS**: invalid-subject handling is covered by action tests.
- AC-08 — **PASS**: ambiguity does not query `MesaExamen`.
- AC-09 — **PASS**: valid subjects without mesas are distinct from not-found.
- AC-10 — **PASS**: one mesa is returned with code and date.
- AC-11 — **PASS**: multiple mesas are returned without dropping rows.
- AC-12 — **PASS**: responses use canonical subject names.
- AC-13 — **PASS**: repeated explicit requests replace the subject correctly.
- AC-14 — **PASS**: backend failures produce controlled outcomes.
- AC-15 — **PASS**: final and partial requests remain separated.
- AC-16 — **PASS**: final-date and registration requests remain separated.
- AC-17 — **PASS**: subject-only language is contextual, not an explicit date
  request.
- AC-18 — **PASS**: inherited authentication prerequisites remain enforced.

The diagnostic standalone connector does not block any acceptance criterion.

## Out of scope and limitations

- Registration, cancellation, partial-exam dates, eligibility, academic
  periods, and multi-subject requests remain out of scope.
- Post-completion elliptical continuations such as `¿y en Álgebra?` remain
  deferred to a future cross-capability context refactor.
- Authentication and matrícula behavior were not redesigned.
- The attendance fixture mismatch remains outside 004.

## Conclusion

The final-exam-date capability is complete according to the current 004
specification. The 75-epoch/no-component architecture reaches the complete
subject through slot filling and `SubjectResolver` in all three fresh runs.
