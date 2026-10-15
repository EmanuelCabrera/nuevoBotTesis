# 008 — Materias cursadas / Course Records — Acceptance Criteria

## AC-01 — Explicit course-record request

**Given** the user explicitly asks for their materias cursadas

**When** the request is classified

**Then** it is recognized as `consultar_materias`.

## AC-02 — Safe general subject-list wording

**Given** the user asks “qué materias tengo” or “mostrame mis materias”

**When** 008 answers

**Then** the result is explicitly described as registered course records, not
as current enrollment.

## AC-03 — Authentication requirement

**Given** `is_authenticated` is false

**When** the action runs

**Then** it does not access Supabase, explains that authentication is required,
and clears `flujo_actual`.

## AC-04 — Matrícula collection

**Given** the user is authenticated but `matricula` is absent

**When** the normal dialogue starts

**Then** `materias_form` requests only `matricula`.

## AC-05 — Existing matrícula reuse

**Given** authentication and `matricula` already exist

**When** the user explicitly requests course records

**Then** the action can run without asking for a subject.

## AC-06 — One course record

**Given** the matrícula has one `MateriaCursada` row

**When** the action succeeds

**Then** it displays the canonical subject name and course date once.

## AC-07 — Multiple course records

**Given** the matrícula has multiple `MateriaCursada` rows

**When** the action succeeds

**Then** it displays every row and reports the raw row count.

## AC-08 — No course records

**Given** the query returns no rows

**When** the action completes

**Then** it reports that no registered course records were found and clears
`flujo_actual`.

## AC-09 — Invalid matrícula limitation

**Given** the matrícula does not identify a visible student

**When** only `MateriaCursada` is queried

**Then** the result remains indistinguishable from a valid student with no
records; no unsupported distinction is claimed.

## AC-10 — Backend error

**Given** Supabase raises an exception

**When** the action runs

**Then** it emits a controlled failure message and clears `flujo_actual`.

## AC-11 — Duplicate handling

**Given** duplicate rows are returned

**When** the action formats the result

**Then** each row is displayed and counted because no verified uniqueness or
product deduplication rule exists.

## AC-12 — Deterministic ordering

**Given** multiple rows are returned

**When** they are displayed

**Then** they are ordered by `fecha_cursada` ascending and canonical subject
name as a deterministic tie-breaker.

## AC-13 — Canonical display names

**Given** a course row relates to `Materia`

**When** it is displayed

**Then** its name comes from `Materia.nombre`, not user input or
`SubjectResolver`.

## AC-14 — State isolation and repeated request

**Given** any terminal action path completes

**When** events are returned

**Then** `flujo_actual` is cleared, `materia` is not modified, and `matricula`
remains available for another explicit request.

## AC-15 — Boundary against grades and attendance

**Given** the user asks for grades or attendance

**When** NLU classifies the request

**Then** it does not route to `consultar_materias`.

## AC-16 — Boundary against requirements and exam operations

**Given** the user asks for requirements, exam dates, exam registration, or
exam-registration cancellation

**When** NLU classifies the request

**Then** it does not route to `consultar_materias`.

## AC-17 — Unsupported and ambiguous semantics

**Given** the user asks about current enrollment, the current semester, or only
says “qué tengo”

**When** the 008 contract is evaluated

**Then** those expressions are not required positives for
`consultar_materias`, and 008 does not claim current-enrollment behavior.
