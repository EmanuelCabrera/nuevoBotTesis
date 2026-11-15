# 010 — Conversation State Cleanup — Acceptance Criteria

## AC-01 — No runtime `flujo_actual`

Production domain, rules, stories, and actions contain no functional
`flujo_actual` definition, read, write, or clear operation.

## AC-02 — Form context

Every multi-turn capability derives its active context from `active_loop` and
`requested_slot` rather than a generic capability marker.

## AC-03 — Valid subject canonicalization

A subject-based form resolves a valid expression with the shared catalog and
resolver and stores the canonical subject name before submission.

## AC-04 — Unknown subject retry

An unknown subject is rejected inside the active form, `materia` becomes null,
and `requested_slot` remains `materia` until corrected.

## AC-05 — Ambiguous subject retry

An ambiguous subject is rejected inside the active form, its candidates are
reported, and `requested_slot` remains `materia` until corrected.

## AC-06 — Catalog/backend error

A catalog failure produces a technical response and remains retryable; it is
not reported as “subject not found”.

## AC-07 — Attendance retry

001 rejects invalid/ambiguous subjects in `asistencia_form` and completes after
a corrected subject without a `flujo_actual` rule.

## AC-08 — Grades retry

002 rejects invalid/ambiguous subjects in `notas_form` and completes after a
corrected subject.

## AC-09 — Requirements runtime contract

003 validates `materia` in `requisitos_form`, does not require matrícula, and
queries `MateriaEquivalencia` by canonical subject code.

## AC-10 — Final-date retry

004 rejects invalid/ambiguous subjects in `consultar_mesas_form` and preserves
its existing no-mesa and backend distinctions.

## AC-11 — Partial-date retry

005 rejects invalid/ambiguous subjects in `fechas_parciales_form` without
changing its authentication, matrícula, or date contract.

## AC-12 — Registration preservation

006 retains its working form validation, mesa selection, canonical subject
resolution, and duplicate-registration policy without generic flow state.

## AC-13 — Cancellation retry

007 rejects invalid/ambiguous subjects in `cancelar_mesa_form` and then
preserves its existing cancellation rules.

## AC-14 — Course-record form ownership

008 follows `consultar_materias → materias_form → matricula → action` without a
legacy continuation rule or SubjectResolver.

## AC-15 — FAQ regression

009 remains `FAQ intent → direct static utterance` without conversational
state changes.

## AC-16 — Business-slot cleanup

Completion behavior continues to clear only the capability's documented
ephemeral business slots; no unrelated slot is cleared.

## AC-17 — Python regression

The complete Python suite passes with assertions about business behavior and
validator results rather than generic state events.

## AC-18 — Core regression and stability

Dedicated Core suites 001–009 and the 010 retry suite pass for three freshly
trained models.

## AC-19 — NLU preservation

Dedicated NLU suites 001–009 show no intentional contract change attributable
to 010.

## AC-20 — Deferred follow-ups

Post-completion elliptical follow-ups are not added or required by this work.

