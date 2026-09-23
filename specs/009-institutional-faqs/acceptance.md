# 009 — Institutional FAQs — Acceptance Criteria

## AC-01 — Explicit FAQ recognition

**Given** a request explicitly identifies one of the 17 documented FAQ topics

**When** NLU classifies it

**Then** it maps to the corresponding institutional intent.

## AC-02 — Correct static response route

**Given** a supported FAQ intent

**When** dialogue prediction runs

**Then** it selects that intent's documented `utter_*` response.

## AC-03 — Administrative admission boundaries

**Given** a request about admission documents, dates, or in-person/remote mode

**When** it is classified

**Then** it remains distinct from final-exam registration and cancellation.

## AC-04 — Course-of-entry information

**Given** an explicit question about the leveling/entry course

**When** it is classified

**Then** it routes to `curso_ingreso` and its static response.

## AC-05 — CONEAU information

**Given** an explicit accreditation/authorization question

**When** it is classified

**Then** it routes to `evaluacion_coneau`.

## AC-06 — Visits versus contacts

**Given** a request about visiting UGD or a request for contact details

**When** it is classified

**Then** visits route to `visitas_consultas` and contact details route to
`contactos`.

## AC-07 — Scholarships

**Given** an explicit scholarship or sibling-discount question

**When** it is classified

**Then** it routes to `informar_becas_hermanos`.

## AC-08 — Working-student accommodations

**Given** an explicit question about schedules for a working student

**When** it is classified

**Then** it routes to `informar_horarios_trabajadores` without being treated as
personal attendance data.

## AC-09 — Exchanges

**Given** an explicit academic-exchange question

**When** it is classified

**Then** it routes to `informar_intercambio_de_estudio`.

## AC-10 — Equivalences versus prerequisites

**Given** recognition of prior studies or a prerequisite request for a specific
subject

**When** it is classified

**Then** recognition routes to `informar_equivalencias` and prerequisites to
`consultar_requerimientos_materia`.

## AC-11 — Exam policy versus exam dates

**Given** a general exam/recovery-policy question or a dated exam request

**When** it is classified

**Then** policy routes to `informar_examen_recuperatorio` and subject-specific
dates remain in capabilities 004/005.

## AC-12 — Attendance policy versus personal attendance

**Given** a question about the institutional attendance rule or a student's
record for a subject

**When** it is classified

**Then** policy routes to `informar_asistencia` and personal records to
`consultar_asistencia`.

## AC-13 — Academic support

**Given** an explicit computing/English support question

**When** it is classified

**Then** it routes to `informar_ayuda_informatica_ingles`.

## AC-14 — Teacher qualifications

**Given** an explicit teacher-qualification question

**When** dialogue completes

**Then** `informar_nivel_profesores` routes to
`utter_respuesta_informar_nivel_profesores`.

## AC-15 — Equipment versus services

**Given** an explicit technology/equipment question or a general services
question

**When** it is classified

**Then** each routes to its distinct documented intent and response.

## AC-16 — Personal academic capabilities

**Given** the user asks for personal grades, attendance, course records, or
subject requirements

**When** NLU classifies the request

**Then** it does not route to an institutional FAQ.

## AC-17 — Transactional capabilities

**Given** the user explicitly requests exam registration or cancellation

**When** NLU classifies the request

**Then** it remains in capabilities 006/007 rather than an admission FAQ.

## AC-18 — Ambiguous generic wording

**Given** only “necesito información”, “ayuda”, “qué necesito”, or equivalent
broad wording

**When** NLU classifies it

**Then** 009 does not require an arbitrary specific FAQ prediction.

## AC-19 — Stateless direct and repeated use

**Given** an explicit FAQ is asked directly or after another FAQ

**When** each response completes

**Then** no authentication, form, requested slot, active loop, or
`flujo_actual` state is introduced.

## AC-20 — Static-response consistency and provenance

**Given** a FAQ is answered

**When** the response is rendered

**Then** it uses the corresponding `domain.yml` template and does not invent
facts beyond it; mutable hard-coded claims remain documented as source-risk.
