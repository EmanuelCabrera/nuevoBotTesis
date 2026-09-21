# 005 — Partial Exam Dates

## 1. Purpose

Define the behavior for consulting the scheduled dates of partial exams for a
subject.

## 2. Scope

This capability covers:

- explicit requests for partial-exam dates;
- requests that include a subject and requests that omit it;
- collection of a missing subject through the partial-dates form;
- canonical subject resolution against the authoritative `Materia` catalog;
- one or multiple partial-date records for a valid subject;
- invalid, ambiguous, no-result, and backend-error outcomes;
- the distinction between institutional partial schedules and personal grades.

Authentication and matrícula remain inherited prerequisites of the current
product flow. They are not redefined by this capability.

## 3. Out of scope

This capability does not cover:

- final-exam or mesa dates;
- exam-table registration or cancellation;
- selecting a particular partial;
- determining whether a student is eligible to take a partial;
- checking grades, attendance, correlatives, or student history;
- interpreting first/second partial semantics when they are not represented by
  the database;
- academic periods, calls, turns, curriculum versions, or schema changes;
- post-completion elliptical follow-ups such as “¿y en Álgebra?”.

## 4. Terminology

- **Partial date:** a scheduled institutional date stored for a subject in
  `Parciales`.
- **Queried subject:** the canonical `Materia` record selected by the user’s
  subject expression.
- **Direct records:** the rows returned from `Parciales` for the queried
  subject’s canonical code.

## 5. Authentication and matrícula

The current implementation requires an authenticated user and a matrícula
before the lookup runs. This is inherited legacy behavior. The database rows
are institutional schedule data and are not student-specific: the partial
table has no `estudiante_id`, and the current query does not filter by
matrícula.

## 6. Data contract

The relevant live table is `Parciales` with these observed columns:

- `id`;
- `created_at`;
- `materia_codigo`;
- `fecha_parcial`;
- `profesor_id`.

`Parciales.materia_codigo` references `Materia.codigo`. Canonical subject
display names come from `Materia`.

The contract does not contain a partial number, assessment type, call, period,
student identifier, or eligibility field. Therefore the capability returns
the direct date rows available for the subject and does not infer any of those
semantics.

## 7. Subject resolution

The intended subject behavior reuses the shared catalog and resolver:

- case and accent differences are normalized;
- Arabic and Roman numbering variants identify the same numbered level;
- an unnumbered numbered family defaults to level I when supported;
- nonexistent levels are not invented;
- invalid subjects produce a subject-not-found outcome;
- ambiguous subjects produce clarification and no `Parciales` query;
- the canonical `Materia.codigo` and display name are preserved.

Language/entity extraction and canonical catalog resolution remain separate
concerns.

## 8. Main flows

### Request with a subject

1. The user asks for partial dates and names a subject.
2. The subject is resolved against the canonical catalog.
3. The assistant does not request the subject again.
4. `Parciales` is queried by canonical `materia_codigo`.
5. All direct records are returned, with their recorded dates.

### Request without a subject

1. The user asks when the partials are without naming a subject.
2. `fechas_parciales_form` requests `materia` (after any inherited matrícula
   prerequisite).
3. A subject-only reply is captured through generic `proporcionar_materia`
   while the form is active.
4. The form completes and the partial-date action runs.

## 9. Multiple partial dates

Multiple `Parciales` rows may exist for one subject. The capability must not
silently discard rows. A deterministic chronological order by
`fecha_parcial` is appropriate when the stored date values are comparable.

The response must not label a row as “first” or “second” as an academic fact;
the database does not provide that field. Any ordinal numbering in current
legacy presentation is display ordering only.

## 10. Alternative and error flows

- **Missing authentication:** preserve the existing authentication response
  and do not query the database.
- **Missing matrícula:** ask for matrícula and preserve the partial-date flow.
- **Subject not found:** report that the subject does not exist and do not query
  `Parciales`.
- **Ambiguous subject:** ask for clarification, do not select an arbitrary
  match, and preserve enough form context to continue.
- **Valid subject without rows:** report that no partial dates are registered
  for the canonical subject; do not report subject-not-found.
- **Backend failure:** return a controlled error; do not fabricate dates or
  reinterpret the error as no results.

## 11. State expectations

- `materia` is the capability-specific conversational input.
- `fechas_parciales_form` remains active while a required subject is missing.
- `requested_slot` identifies `materia` when the form asks for it.
- A successful lookup clears stale `materia` and `flujo_actual` according to
  the established action cleanup pattern.
- Missing, ambiguous, and backend-error paths must not silently leave a
  successful-completion state that contaminates the next request.

## 12. Semantic boundaries

### Partial dates versus final dates

Explicit references to “parcial” or “parciales” belong here. “Final”, “mesa”,
or “mesas” belong to final-exam-date consultation.

### Partial dates versus registration

Asking when a partial occurs is a date query. Asking to register, enroll, or
reserve a place is a registration request.

### Partial dates versus grades

“Qué nota saqué” or “mis calificaciones” asks for grades, not a schedule.

### Subject-only language

A standalone subject does not independently express a partial-date request. It
continues this capability only while `fechas_parciales_form` is actively
requesting `materia`.

### Generic exam wording

“¿Cuándo es el examen?” is ambiguous between partial and final dates unless the
conversation or explicit terminology supplies the distinction.

## 13. Representative examples

```text
¿Cuándo es el parcial de Física II?
¿Qué fecha tiene el segundo parcial de Redes de Computadoras II?
¿Cuándo son los parciales?
```

Missing-subject flow:

```text
Usuario: ¿Cuándo son los parciales?
Asistente: ¿De qué materia quieres consultar las fechas?
Usuario: Física II
```
