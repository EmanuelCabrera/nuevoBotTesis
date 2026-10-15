# 009 — Institutional FAQs — Results

## Final contract

Capability 009 provides 17 static institutional FAQs. Each supported request
is a stateless one-turn route:

```text
explicit FAQ intent
→ direct Rasa rule
→ existing domain.yml utterance
```

No form, slot, entity, custom action, authentication state, `flujo_actual`,
Supabase query, or new institutional fact was introduced.

## Routing cleanup

One direct rule now owns each FAQ route. The historical FAQ-only stories were
removed because they were redundant once the rules existed; unrelated stories
remain.

| Intent | Direct rule | Utterance | Deterministic |
|---|---|---|---|
| `requisitos_inscripcion` | FAQ requisitos de inscripción | `utter_respuesta_requisito_inscripcion` | yes |
| `plazos_inscripcion` | FAQ plazos de inscripción | `utter_respuesta_plazos_inscripcion` | yes |
| `evaluacion_coneau` | FAQ evaluación CONEAU | `utter_respuesta_evaluacion_coneau` | yes |
| `curso_ingreso` | FAQ curso de ingreso | `utter_respuesta_curso_ingreso` | yes |
| `informar_modalidad_inscripcion` | FAQ modalidad de inscripción | `utter_respuesta_informar_modalidad_inscripcion` | yes |
| `visitas_consultas` | FAQ visitas | `utter_respuesta_visitas_consultas` | yes |
| `informar_becas_hermanos` | FAQ becas | `utter_respuesta_informar_becas_hermanos` | yes |
| `informar_horarios_trabajadores` | FAQ horarios para trabajadores | `utter_respuesta_informar_horarios_trabajadores` | yes |
| `informar_intercambio_de_estudio` | FAQ intercambio | `utter_respuesta_intercambio_de_estudio` | yes |
| `informar_equivalencias` | FAQ equivalencias | `utter_respuesta_equivalencias` | yes |
| `informar_examen_recuperatorio` | FAQ exámenes y recuperatorios | `utter_respuesta_examen_recuperatorio` | yes |
| `informar_asistencia` | FAQ régimen de asistencia | `utter_respuesta_asistencia` | yes |
| `informar_ayuda_informatica_ingles` | FAQ apoyo en informática e inglés | `utter_respuesta_informar_ayuda_informatica_ingles` | yes |
| `informar_nivel_profesores` | FAQ nivel de profesores | `utter_respuesta_informar_nivel_profesores` | yes |
| `informar_equipamiento_tecnologico` | FAQ equipamiento tecnológico | `utter_respuesta_informar_equipamiento_tecnologico` | yes |
| `informar_servicios` | FAQ servicios | `utter_respuesta_informar_servicios` | yes |
| `contactos` | FAQ contactos | `utter_contactos` | yes |

This resolves all three baseline Core failures:
`informar_nivel_profesores`, `plazos_inscripcion`, and `curso_ingreso`.

## Baseline NLU failures and disposition

| Held-out text | Expected | Baseline prediction | Classification | Disposition |
|---|---|---|---|---|
| “en qué meses abre la inscripción universitaria” | `plazos_inscripcion` | `requisitos_inscripcion` (0.4510) | A: missing representative coverage | Added natural month/period coverage. |
| “puedo recorrer la universidad antes de inscribirme” | `visitas_consultas` | `inscribirse_mesa_examen` (0.2016) | D: functional overlap | Visit examples now consistently describe institutional visits. |
| “los parciales tienen recuperatorio” | `informar_examen_recuperatorio` | `consultar_fechas_parciales` (0.6947) | D: functional overlap | Added explicit general recuperatorio-policy coverage. |
| “cuál es la modalidad general de los exámenes y la nota mínima” | `informar_examen_recuperatorio` | `consultar_notas` (0.5416) | D: functional overlap | Added general modality and passing-grade wording. |
| “qué formación académica tienen los docentes” | `informar_nivel_profesores` | `informar_modalidad_inscripcion` (0.5389) | A: missing representative coverage | Replaced subjective/CV wording with qualification wording. |
| “qué servicios institucionales tienen los estudiantes” | `informar_servicios` | `informar_asistencia` (0.9175) | C: FAQ overlap | Services examples now name only services present in the response. |
| “dónde encuentro los teléfonos de las sedes” | `contactos` | `inscribirse_mesa_examen` (0.2976) | A: sparse contact coverage | Expanded contact examples from 5 to 10 without adding contact facts. |

## Production NLU cleanup

No examples were moved into a new intent and no new intent was created.
Misleading examples were rewritten or removed in these areas:

- admission requirements no longer mix subjects, exam tables, or finals;
- visits no longer promise rector/professor interviews, guided visits, or
  class observation that the utterance does not answer;
- working-student examples focus on schedule/coursing compatibility rather
  than undocumented absence justification;
- equivalence examples consistently ask whether UGD recognizes prior studies;
- exchange examples no longer ask about career changes, prices, or unsupported
  destinations;
- exam examples no longer ask for curriculum plans or unsupported exam counts;
- computing/English support examples explicitly mention those areas;
- teacher examples ask about qualifications rather than subjective quality or
  individual CV access;
- equipment examples refer to technology rather than generic facilities;
- services examples no longer promise careers, housing, buffet, pool, or an
  institution-owned gym;
- attendance policy was deduplicated and rebalanced around policy words such
  as percentage, regulation, and allowed absences;
- contact coverage was expanded around the existing directory-link response.

Final production counts (**393 examples total**):

| Intent | Examples |
|---|---:|
| `requisitos_inscripcion` | 29 |
| `plazos_inscripcion` | 26 |
| `evaluacion_coneau` | 28 |
| `curso_ingreso` | 31 |
| `informar_modalidad_inscripcion` | 28 |
| `visitas_consultas` | 27 |
| `informar_becas_hermanos` | 26 |
| `informar_horarios_trabajadores` | 26 |
| `informar_intercambio_de_estudio` | 14 |
| `informar_equivalencias` | 15 |
| `informar_examen_recuperatorio` | 15 |
| `informar_asistencia` | 67 |
| `informar_ayuda_informatica_ingles` | 12 |
| `informar_nivel_profesores` | 13 |
| `informar_equipamiento_tecnologico` | 13 |
| `informar_servicios` | 13 |
| `contactos` | 10 |

## Generic-language diagnostic

The project already has `FallbackClassifier` with threshold `0.3`, ambiguity
threshold `0.1`, an `nlu_fallback` rule, and `utter_please_rephrase`. No new
`out_of_scope` intent or global threshold change was introduced.

The six generic diagnostics are excluded from supported FAQ acceptance. In
the final full pipeline:

- run 1: fallback for 4/6;
- run 2: fallback for 4/6;
- run 3: fallback for 2/6.

“ayuda” still tends to `informar_ayuda_informatica_ingles`; “qué necesito” and
“qué opciones tengo” may still map to specific intents. Fixing this safely
requires a cross-capability fallback/help decision, because increasing the
global fallback threshold would affect capabilities 001–008. This remains
deferred and is not treated as supported FAQ language.

## Validation results

Environment: Python 3.9.12, Rasa 3.6.20, Rasa SDK 3.6.2, DIETClassifier with
75 epochs.

- `rasa data validate`: PASS; no story conflicts.
- Initial corrected NLU: **45/55 overall**, comprising **45/49 supported** and
  **0/6 generic diagnostics**.
- Final Core: **19/19 conversations, 42/42 actions**.
- FAQ action tests: not applicable; no custom FAQ action exists.
- Full Python: **132/133**. The only failure is the pre-existing Attendance
  fixture `test_no_matching_subject`, which expects `flujo_actual` cleanup
  while production clears `materia`.

### Three-run NLU stability

| Run | Overall | Supported FAQ + boundaries | Generic diagnostic |
|---|---:|---:|---:|
| 1 | 49/55 | 49/49 | 0/6 as labelled `out_of_scope`; 4/6 use runtime fallback |
| 2 | 49/55 | 49/49 | 0/6 as labelled `out_of_scope`; 4/6 use runtime fallback |
| 3 | 49/55 | 49/49 | 0/6 as labelled `out_of_scope`; 2/6 use runtime fallback |

Every FAQ intent has recall 1.0 in the reference run. Four intents have lower
precision only because generic diagnostics become false positives:
`informar_ayuda_informatica_ingles` (P/R/F1 0.50/1.00/0.67),
`requisitos_inscripcion`, `informar_horarios_trabajadores`, and
`informar_servicios` (each 0.67/1.00/0.80). The other 13 FAQ intents are
1.00/1.00/1.00.

### Regression controls

| Capability | NLU | Core conversations | Core actions |
|---|---:|---:|---:|
| 001 Attendance | 27/28 | 4/4 | 19/19 |
| 002 Grades | 15/18 | 5/5 | 27/27 |
| 003 Subject Requirements | 21/22 | 6/6 | 31/31 |
| 004 Final Exam Dates | 24/24 | 5/5 | 26/26 |
| 005 Partial Exam Dates | 27/27 | 5/5 | 25/25 |
| 006 Final Exam Registration | 28/28 | 5/5 | 23/23 |
| 007 Final Exam Cancellation | 19/19 | 5/5 | 20/20 |
| 008 Course Records | 23/25 | 5/5 | 20/20 |

Core regression total: **40/40 conversations and 191/191 actions**. The NLU
misses are existing suite fluctuations; no completed-capability request in
the dedicated 009 boundary set is stolen by an FAQ.

## Acceptance review

| AC | Status | Evidence |
|---|---|---|
| AC-01 | PASS | 37/37 explicit FAQ cases pass in all final runs. |
| AC-02 | PASS | All 17 direct routes select the documented utterance. |
| AC-03 | PASS | Admission remains separate from exam registration/cancellation. |
| AC-04 | PASS | `curso_ingreso` routes directly. |
| AC-05 | PASS | CONEAU questions route directly. |
| AC-06 | PASS | Visits and contacts are distinct in the final supported suite. |
| AC-07 | PASS | Scholarship/sibling-discount questions route correctly. |
| AC-08 | PASS | Working-student schedule questions route correctly. |
| AC-09 | PASS | Supported exchange questions route correctly. |
| AC-10 | PASS | Equivalence and subject prerequisites remain distinct. |
| AC-11 | PASS | General exam policy remains separate from subject dates. |
| AC-12 | PASS | Policy and personal attendance contrasts pass. |
| AC-13 | PASS | Computing/English support requires explicit context. |
| AC-14 | PASS | Missing teacher-qualification route is fixed. |
| AC-15 | PASS | Equipment and services remain distinct. |
| AC-16 | PASS | Personal academic contrasts pass 8/8 in the dedicated suite. |
| AC-17 | PASS | Registration/cancellation remain transactional intents. |
| AC-18 | DEFERRED | Generic fallback is seed-dependent and requires a global help/fallback decision. |
| AC-19 | PASS | Direct and repeated FAQ Core stories pass without state. |
| AC-20 | PASS | Existing utterances were preserved and source risk is documented. |

Unsupported questions removed from the FAQ promise—individual staff
interviews/CVs, housing, buffet, pool, exchange prices, career-change fees,
and similar content—are **OUT OF SCOPE** because no repository-backed answer
exists.

## Remaining limitations and completion decision

Sixteen answers remain static institutional information stored in `domain.yml`
with no independent repository source or update date. `contactos` remains the
only source-class A response because it links to the institutional directory.
This is a maintenance limitation, not a blocker for the thesis capability.

Capability 009 can be marked **DONE for its explicit supported FAQ contract**:
routing is deterministic, supported NLU is stable across three runs, and Core
and regression controls pass. Generic help/fallback behavior remains a
documented cross-capability deferred item.

Suggested commit message:

```text
feat(009): estabilizar rutas y limpiar NLU de FAQs institucionales
```
