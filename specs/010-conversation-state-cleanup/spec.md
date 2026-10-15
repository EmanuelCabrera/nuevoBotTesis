# 010 — Conversation State Cleanup — Specification

## Purpose

Capability 010 is a transversal architecture cleanup across capabilities
001–009. It removes the generic `flujo_actual` marker and makes each form own
its collection and retry context through `active_loop`, `requested_slot`, and
business slots.

This work does not introduce a new product capability and does not intentionally
change NLU semantics or the completed capabilities' business contracts.

## Target architecture

```text
explicit capability intent
→ capability form
→ requested business slot
→ shared subject validation and canonicalization, when applicable
→ submit only with valid input
→ business action
```

`active_loop` and `requested_slot` are the authoritative conversational state
while a form is active. `matricula`, `materia`, `fecha_mesa`, and
`codigo_mesa_examen` remain business data; no second generic “current
capability” slot is maintained.

## Subject validation contract

Forms that collect `materia` validate it against `SubjectCatalogRepository`
through `SubjectResolver` before submission.

- A valid expression is stored as its canonical subject name.
- An unknown expression produces the existing controlled not-found response,
  clears `materia`, and leaves the form requesting `materia`.
- An ambiguous expression lists the canonical candidates, clears `materia`,
  and leaves the form requesting `materia`.
- A catalog/backend failure produces a technical response rather than a false
  not-found result, clears the attempted value, and permits a retry.

Business actions retain defensive validation for calls made outside the normal
form route, but normal form-owned calls receive canonical subject input.

## Capability scope

- 001 Attendance: form-owned subject retry.
- 002 Grades: form-owned subject retry.
- 003 Subject Requirements: form-owned subject retry; requirements remain a
  curricular lookup by subject.
- 004 Final Exam Dates: form-owned subject retry.
- 005 Partial Exam Dates: form-owned subject retry; authentication and
  matrícula behavior remain otherwise unchanged.
- 006 Final Exam Registration: preserve its existing validator and remove only
  redundant generic state events.
- 007 Final Exam Cancellation: add form-owned subject validation.
- 008 Course Records: keep matrícula-only form collection and remove the legacy
  action continuation rule.
- 009 Institutional FAQs: remain stateless direct rules.

## Requirements and matrícula

`MateriaEquivalencia` is queried only by canonical `materia_codigo`. A student
matrícula does not participate in the query, authorization, authentication, or
any requirements business rule. Capability 003 therefore requires
authentication and subject input, but not matrícula.

## Explicit non-goals

- Post-completion elliptical follow-ups such as “¿y en Física?”.
- Generic help/fallback redesign.
- Generic date clarification such as “fecha de Física II”.
- Partial number, partial type, or recuperatorio support.
- Global authentication/matrícula architecture cleanup.
- Final-exam re-enrollment policy after `baja=true`.
- Intent, entity, or production NLU redesign.

