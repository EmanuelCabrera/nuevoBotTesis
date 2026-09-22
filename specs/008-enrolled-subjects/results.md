# 008 — Materias cursadas / Course Records — Results

## Final contract

Capability 008 implements the documented product requirement:

> Consultar materias cursadas por matrícula.

“Materias cursadas” means every visible `MateriaCursada` record associated with
the student's matrícula. It does not mean current enrollment, current-semester
subjects, approved-only subjects, or the complete curriculum.

The directory keeps its existing `008-enrolled-subjects` name to avoid an
unnecessary move, but the capability name and specification are now **Materias
cursadas / Course Records**.

## Semantic mismatch corrected

Before this change, 14 of the 36 `consultar_materias` examples promised
current-course or current-period semantics through expressions such as
“materias en curso”, “estoy cursando”, “materias actuales”, “este
cuatrimestre”, and “este semestre”. The action actually returned historical
`MateriaCursada` rows without a period or active-enrollment filter.

All 14 examples were rewritten as natural course-record requests. The final
production count remains 36: the cleanup changes meaning without inflating the
dataset with repetitive examples.

| Unsupported wording before | Aligned wording after |
|---|---|
| necesito ver mis materias en curso | quiero ver las materias que cursé |
| cuales son mis materias actuales | cuales son mis materias cursadas |
| dime que materias estoy cursando | dime que materias cursé |
| cuales son mis materias del cuatrimestre | que materias figuran como cursadas |
| dime mis materias en curso | mostrame mis materias cursadas |
| cuales son las materias que estoy cursando | cuales son las materias que cursé |
| quiero saber que materias tengo este cuatrimestre | quiero saber que materias tengo registradas como cursadas |
| quiero consultar que materias estoy cursando | quiero consultar mi historial de cursadas |
| necesito saber mis materias en curso | necesito saber que materias cursé |
| cuales materias tengo este semestre | que materias aparecen en mi historial de cursadas |
| quiero consultar mis materias actuales | quiero consultar mis materias cursadas |
| dime que materias tengo en curso | dime que materias figuran como cursadas |
| materias en curso matricula 66031 | materias cursadas matricula 66031 |
| materias en curso con matricula 66031 | materias cursadas con matricula 66031 |

The dedicated acceptance dataset now contains 10 positive 008 examples:

- five explicit course-record requests;
- three safe general subject-list requests;
- two requests with a `matricula` entity.

The bare phrase “qué tengo” was removed from the dedicated dataset entirely.
It is neither a positive 008 requirement nor forced into another capability.

## Final action architecture

```text
consultar_materias
→ existing matrícula or materias_form
→ authentication and matrícula checks
→ MateriaCursada filtered by estudiante
→ related Materia.nombre
→ deterministic course-record response
```

`matricula` remains the only functional input. The action does not use
`SubjectResolver`, does not request `materia`, and applies no period, status,
or `aprobada` filter.

Returned rows are sorted by `fecha_cursada` ascending and then canonical
subject name. Rows are not deduplicated: no verified uniqueness constraint or
product deduplication rule exists, so every returned record is displayed and
counted.

The response explicitly calls the data “registros de materias cursadas”.

## State behavior

- Success: clear `flujo_actual`; preserve `matricula` and `materia`.
- No records: report the empty course-record result and clear `flujo_actual`.
- Authentication failure: do not query Supabase and clear `flujo_actual`.
- Backend failure: emit a controlled error and clear `flujo_actual`.
- Missing matrícula on direct invocation: request matrícula and retain
  `flujo_actual=consultar_materias` for the existing continuation path.

The legacy `flujo_actual` continuation rule remains. `materias_form` owns the
normal interaction, but removing shared continuation behavior was not needed
to satisfy the contract and would broaden this feature's risk.

## Environment and validation

- Python: 3.9.12.
- Rasa: 3.6.20.
- Rasa SDK: 3.6.2.
- DIET epochs: 75.
- Fresh full model:
  `/private/tmp/nuevoBotTesis_008_course_records_20260922/initial/008_initial.tar.gz`.
- `rasa data validate`: passed with only the repository's existing unused
  intent/utterance warnings.

## Initial dedicated verification

The corrected 25-example mixed NLU suite produced:

- overall: **22/25 (88%)**;
- `consultar_materias`: **10/10**, precision 100%, recall 100%, F1 100%;
- `matricula`: precision 100%, recall 100%, F1 100% over two entities;
- grades contrasts: 3/4;
- attendance contrasts: 2/3;
- exam-related contrasts: 5/6.

The three initial errors were unrelated to recognition of 008:

- “cuánto saqué en Álgebra”: `consultar_notas` → `proporcionar_materia`;
- “cuántas faltas tengo”: `consultar_asistencia` → `informar_asistencia`;
- “a qué finales estoy inscripto”: unsupported `out_of_scope` →
  `inscribirse_mesa_examen`.

No example was incorrectly predicted as `consultar_materias`, and all ten 008
positives passed.

Dedicated Core passed **5/5 conversations** and **20/20 actions**. Dedicated
action tests passed **10/10**.

## Three-run NLU stability

Three NLU-only models were trained independently. Separate
`RASA_CACHE_DIRECTORY` values were used for runs 2 and 3 so DIET and all NLU
components were genuinely retrained rather than restored from Rasa's cache.

| Run | Overall | `consultar_materias` P/R/F1 | `matricula` P/R/F1 | Grades | Attendance | Exam-related |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 23/25 | 100/100/100 | 100/100/100 | 3/4 | 3/3 | 5/6 |
| 2 | 23/25 | 100/100/100 | 100/100/100 | 3/4 | 3/3 | 5/6 |
| 3 | 23/25 | 100/100/100 | 100/100/100 | 3/4 | 3/3 | 5/6 |

All ten 008 positives and both matrícula entities passed in every run. The two
stable errors were the unrelated grades boundary “cuánto saqué en Álgebra” and
the unsupported final-registration listing “a qué finales estoy inscripto”.

## Regression controls

The fresh full model produced:

| Capability | NLU | Core conversations | Core actions |
|---|---:|---:|---:|
| 001 Attendance | 25/28 | 4/4 | 19/19 |
| 002 Grades | 15/18 | 5/5 | 27/27 |
| 003 Subject Requirements | 19/22 | 6/6 | 31/31 |
| 004 Final Exam Dates | 24/24 | 5/5 | 26/26 |
| 005 Partial Exam Dates | 26/27 | 5/5 | 25/25 |
| 006 Final Exam Registration | 27/28 | 5/5 | 23/23 |
| 007 Final Exam Cancellation | 19/19 | 5/5 | 20/20 |
| **Total** | **155/166** | **35/35** | **171/171** |

No regression error was predicted as `consultar_materias`. The NLU misses are
known cross-capability fluctuations in historical held-out suites and were not
addressed from 008. All dialogue controls remain green.

## Full Python suite

The full suite produced **132/133**. The only failure is the pre-existing,
unrelated attendance fixture mismatch in `test_no_matching_subject`: the test
expects `flujo_actual: None`, while the attendance action returns
`materia: None`.

The dedicated 008 action suite passes **10/10** inside that run.

## Database limitations

- A nonexistent matrícula cannot be distinguished from a valid student with
  zero `MateriaCursada` rows by the current query alone.
- No active enrollment or academic-period semantics can be derived.
- No uniqueness constraint was verifiable with the available Supabase key.
- Duplicate rows are therefore preserved.

These limitations are documented rather than hidden with invented behavior.

## Acceptance status

All **17/17** acceptance criteria are satisfied under the documented course
records contract. Capability 008 can be marked **DONE**, with the database
limitations above remaining explicit non-blocking constraints.
