# Personal Attendance Capability — Pre-Change Baseline

## Purpose of this record

This document records the already measured behavior of the personal-attendance capability before implementation changes. It is historical evidence of the pre-change state.

The measurements below are preserved as originally recorded. They are not updated, rerun, or reinterpreted in this document.

## NLU evaluation

| Measurement | Baseline result |
|---|---:|
| Cases passed | 10/28 |
| Overall accuracy | 35.7% |
| Personal-attendance cases correct | 10/19 |
| Personal-attendance recall | 52.6% |
| General attendance-policy cases correct | 0/9 |
| `materia` entity F1 | 72.2% |

### Important NLU failures

| Input | Observed classification |
|---|---|
| “¿Cuántas faltas tengo en Física?” | `consultar_notas` |
| “¿Cuántas veces falté a Física?” | `plazos_inscripcion` |
| “decime cuántas veces no fui a física” | `proporcionar_materia_para_notas` |
| “faltas de física” | `proporcionar_materia_para_asistencia` |
| “¿Y en Matemática?” | `informar_ayuda_informatica_ingles` |
| “¿Cuál es el porcentaje mínimo de asistencia?” | Incorrectly classified as personal attendance |
| “¿Cuántas faltas puedo tener?” | `plazos_inscripcion` |

None of the nine general attendance-policy examples were classified as `informar_asistencia`.

## Entity extraction observations

- `materia` extraction failed in several accented or title-cased examples.
- The multiword subject `Redes de Computadoras 1` was captured.
- The model also incorrectly extracted `veces asistí` as another subject.
- The current evaluation does not yet fully validate canonical subject resolution or ambiguity handling.

## Conversation regression

| Measurement | Baseline result |
|---|---:|
| Attendance scenarios passed | 2/4 |
| Attendance scenarios failed | 2/4 |

Observed scenario results:

- The missing-subject flow passed.
- The general-policy Core test passed when the intent was supplied directly.
- The full personal-attendance request failed.
- The repeated query with a subject change failed.
- In the failed scenarios, Core predicted `action_listen` after `asistencia_form` instead of completing the flow and executing `action_consultar_asistencia`.

## Custom action tests

The custom action tests passed 6/6.

The passing coverage included:

- Successful query behavior.
- Present and absent calculation.
- Total calculation.
- Percentage calculation.
- Missing inputs.
- Unknown subject.
- No attendance records.
- Backend error handling.

### Known action-level weaknesses

- Partial subject matching selects the first result.
- Missing or false `is_present` values may be treated as absences.
- State cleanup after backend exceptions is inconsistent.

## Pre-existing Core suite

| Measurement | Baseline result |
|---|---:|
| Conversations passed | 4/8 |
| Conversation accuracy | 50% |
| Action-level accuracy | 79.4% |

## Coverage gaps in the baseline

- Canonical subject resolution is not yet measured.
- Accent and case normalization is only partially measured.
- Roman and Arabic numeral equivalence is not yet measured.
- Ambiguous subjects such as `Física` versus `Física I` and `Física II` are not yet measured.

## Baseline conclusions

- NLU is currently the largest weakness.
- Personal attendance and general attendance policy are not reliably separated.
- Absence-oriented language is poorly recognized.
- `materia` extraction is not robust enough.
- Contextual subject follow-ups fail.
- Dialogue does not consistently complete the attendance flow.
- Custom action calculation behavior is comparatively stable.
