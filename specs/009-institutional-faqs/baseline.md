# 009 — Institutional FAQs — Audit Baseline

## Scope

This section records the FAQ/institutional implementation before the 009
routing cleanup. The original snapshot is intentionally preserved below;
post-cleanup behavior is documented separately in `results.md`.

## Inventory

The current catalog contains **17 intents and 417 production NLU examples**:

| Intent | Examples | Delivery |
|---|---:|---|
| `requisitos_inscripcion` | 29 | static utterance via story |
| `plazos_inscripcion` | 26 | static utterance via story |
| `evaluacion_coneau` | 28 | static utterance via story |
| `curso_ingreso` | 31 | static utterance via story |
| `informar_modalidad_inscripcion` | 28 | static utterance via story |
| `visitas_consultas` | 27 | static utterance via story |
| `informar_becas_hermanos` | 26 | static utterance via story |
| `informar_horarios_trabajadores` | 24 | static utterance via story |
| `informar_intercambio_de_estudio` | 14 | static utterance via story |
| `informar_equivalencias` | 15 | static utterance via story |
| `informar_examen_recuperatorio` | 14 | static utterance via story |
| `informar_asistencia` | 99 | static utterance via story |
| `informar_ayuda_informatica_ingles` | 12 | static utterance via story |
| `informar_nivel_profesores` | 13 | static utterance; no story/rule |
| `informar_equipamiento_tecnologico` | 13 | static utterance via story |
| `informar_servicios` | 13 | static utterance via story |
| `contactos` | 5 | static utterance via story |

No FAQ entity, slot, form, action, authentication path, `active_loop`, or
`flujo_actual` marker exists. No FAQ reads Supabase.

## Source-of-truth finding

Sixteen responses contain hard-coded institutional claims without an
independent supporting repository/data source or freshness timestamp (class B).
`contactos` points to the official contact directory instead of embedding
mutable details (class A). README confirms broad feature categories but not the
detailed facts.

## Current semantic issues

1. `informar_nivel_profesores` is unreachable through the trained dialogue
   graph because no story/rule connects it to its response.
2. Admission intents contain examples such as “Cómo me inscribo? materia,
   curso, final...” and “materias, mesas, talleres”, overlapping transactional
   final-exam intents and subject prerequisites.
3. `informar_horarios_trabajadores` mixes schedules, attendance exceptions,
   absence justification, and modality claims; it overlaps
   `informar_asistencia` and potentially personal attendance.
4. `informar_intercambio_de_estudio` contains a change-of-career and enrollment
   cost question unrelated to academic exchange.
5. `informar_equivalencias` contains a declarative answer rather than a user
   question and includes recognition in the opposite direction (another
   university recognizing UGD subjects).
6. `informar_examen_recuperatorio` includes “cual es el plan de estudios”,
   which its response does not answer, and broad exam-count questions that may
   overlap date/schedule capabilities.
7. `informar_ayuda_informatica_ingles` contains generic academic-support
   examples without computing or English context.
8. `informar_nivel_profesores` contains subjective “son buenos/idóneos” claims
   that its factual qualification response cannot establish.
9. `informar_equipamiento_tecnologico` contains the broad “cómo funcionan las
   instalaciones”.
10. `informar_servicios` contains “qué carreras tiene la Facultad” and specific
    buffet, housing, gym, pool, and dining questions that the response does not
    reliably answer.
11. `visitas_consultas` promises interviews, guided visits, class observation,
    and access to professors/rector, while its response only says the doors are
    open.
12. Many static facts are time-sensitive and have no provenance metadata.

## Existing coverage before 009

- Attendance NLU and Core suites cover the policy-versus-personal attendance
  boundary, including one `informar_asistencia` dialogue.
- The requirements NLU suite contains contrasts for
  `requisitos_inscripcion` and `informar_equivalencias`.
- No FAQ-wide NLU suite existed.
- No dialogue suite covered all FAQ routes or repeated FAQ requests.
- No test asserted institutional response text.
- No action tests are applicable because FAQ delivery uses domain utterances.

## Dedicated baseline suites

- `tests/nlu_institutional_faqs_test.yml`: 55 held-out examples covering all
  17 FAQ intents, eight completed-capability contrasts, and six deliberately
  ambiguous generic expressions.
- `tests/test_institutional_faqs_stories.yml`: direct routes for all 17 intents,
  one greeting context, and one repeated-FAQ conversation.

The dedicated suite was expanded during cleanup with explicit policy,
equivalence, subject-requirement, exam-date, and attendance-boundary cases.

## Baseline execution

Environment and model:

- Python 3.9.12
- Rasa 3.6.20 / Rasa SDK 3.6.2
- fresh model trained with the configured 75 DIET epochs
- model artifact: `/private/tmp/nuevoBotTesis_009_baseline_20260922/009_baseline.tar.gz`

Validation and dedicated 009 results:

- `rasa data validate`: passed; no story conflicts. It warned that
  `informar_nivel_profesores` and
  `utter_respuesta_informar_nivel_profesores` are unused, in addition to
  pre-existing unused-intent/utterance warnings.
- NLU: **35/48 (72.92%)** overall.
  - Explicit FAQ cases: **27/34**.
  - Completed-capability contrasts: **8/8**.
  - Deliberately generic `out_of_scope` cases: **0/6**; every phrase was
    forced into a specific production intent.
  - The seven missed FAQ cases were one each for `plazos_inscripcion`,
    `visitas_consultas`, `informar_nivel_profesores`, `informar_servicios`,
    and `contactos`, plus two for `informar_examen_recuperatorio`.
- Core: **16/19 conversations (84.21%)** and **39/42 actions (92.86%)**.
  The direct routes for `informar_nivel_profesores`, `plazos_inscripcion`, and
  `curso_ingreso` predicted `action_default_fallback`.
- FAQ action tests: not applicable; no custom FAQ action exists.
- Full Python suite: **132/133 passed**. The sole failure is the pre-existing
  Attendance assertion in
  `test_action_consultar_asistencia.ActionConsultarAsistenciaTests.test_no_matching_subject`:
  production clears `materia`, while the test expects `flujo_actual`.

Regression controls, all evaluated with the same fresh model:

| Capability | NLU | Core conversations | Core actions |
|---|---:|---:|---:|
| 001 Attendance | 27/28 | 4/4 | 19/19 |
| 002 Grades | 15/18 | 5/5 | 27/27 |
| 003 Requirements | 21/22 | 6/6 | 31/31 |
| 004 Final Exam Dates | 24/24 | 5/5 | 26/26 |
| 005 Partial Exam Dates | 27/27 | 5/5 | 25/25 |
| 006 Final Exam Registration | 28/28 | 5/5 | 23/23 |
| 007 Final Exam Cancellation | 19/19 | 5/5 | 20/20 |
| 008 Course Records | 22/25 | 5/5 | 20/20 |

Core regression total: **40/40 conversations and 191/191 actions**. NLU
fluctuations are recorded as baseline observations only; no completed
capability was changed in this branch.

## Smallest recommended refactor order

1. Decide and document an authoritative, maintainable source for mutable
   institutional facts before editing their wording.
2. Add the missing dialogue route for `informar_nivel_profesores` if that FAQ is
   still approved.
3. Remove or rewrite examples whose questions are unrelated to, broader than,
   or unanswered by their response.
4. Harden only evidenced semantic boundaries: admission versus exam
   transactions, policy versus personal attendance, exam policy versus dates,
   services versus equipment, and visits versus contacts.
5. Keep the 17 intents separate unless post-cleanup evaluation demonstrates a
   real indistinguishable boundary; do not merge them only for neatness.
