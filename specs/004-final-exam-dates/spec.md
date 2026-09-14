# 004 — Final Exam Dates

## 1. Purpose

Define the expected behavior when a user asks for available final-exam or exam-table dates for a subject.

## 2. Scope

This capability covers:

- explicit final-exam and exam-table date queries;
- a subject included in the initial request;
- collection of a missing subject;
- one or multiple available exam tables for a valid subject;
- canonical subject resolution;
- invalid, ambiguous, no-result, and backend-error outcomes;
- replacement of a previously queried subject.

## 3. Out of scope

This capability does not cover:

- registration for an exam table;
- cancellation of a registration;
- selection of a table;
- partial-exam dates;
- eligibility to take a final exam;
- checking grades, correlatives, or student history;
- academic-period, call, turn, or curriculum-version redesign;
- changes to the Supabase schema.

## 4. Authentication

The current system requires authentication before returning exam-table dates. This inherited prerequisite remains unchanged. A matrícula is not required by the current final-date consultation flow.

## 5. Subject resolution

The subject expression must resolve against the authoritative `Materia` catalog using the shared subject-resolution contract:

- case and accent differences are ignored;
- Arabic and Roman numbering variants identify the same level when supported by the catalog;
- an unnumbered expression defaults to level I of a numbered family when available;
- distinct numbered levels are never merged;
- nonexistent levels are not invented;
- canonical subject code and display name are preserved;
- ambiguity results in clarification rather than arbitrary selection.

Language recognition and canonical catalog resolution are separate concerns.

## 6. Database contract

`MesaExamen` provides the exam tables for this capability. Relevant fields are:

- `codigo`: authoritative table identifier;
- `fecha`: recorded exam-table date;
- `materia_codigo`: reference to `Materia.codigo`;
- `presidente` and `primer_vocal`: existing table metadata, not required in the response.

The lookup relationship is:

```text
MesaExamen.materia_codigo → Materia.codigo
```

The capability must not infer an academic period, exam type, call, turn, eligibility, or status that is not represented by this contract.

## 7. Main flows

### Request with a subject

1. The user asks for final-exam or mesa dates and names a subject.
2. The subject is identified and resolved canonically.
3. The assistant does not ask for the subject again.
4. Available `MesaExamen` records for the canonical subject are obtained.
5. Every available mesa is returned with its code and date.

### Request without a subject

1. The user asks for final-exam or mesa dates without naming a subject.
2. The assistant asks for the subject.
3. The original final-date flow remains active.
4. A subject-only reply continues that flow.

## 8. Multiple mesas

One subject may have multiple exam-table records. The response must not silently discard any available record. Every returned mesa preserves its authoritative `codigo` and `fecha`.

No chronological ordering requirement is imposed until the product confirms that ordering is part of the contract.

## 9. Alternative and error flows

- **Subject not found:** report that the subject does not exist; do not report it as a valid subject without mesas.
- **Ambiguous subject:** ask for clarification and do not query exam tables until resolution succeeds.
- **Valid subject without mesas:** report that no exam tables are registered for the canonical subject.
- **Backend failure:** return a controlled error and do not fabricate a subject, table, code, or date.
- **Missing authentication:** preserve the inherited authentication requirement.

## 10. Form and state behavior

- `materia` is the only capability-specific conversational input.
- When `materia` is missing, subject collection remains active until the slot is provided.
- A subject-only response is interpreted through active conversation context, not as an explicit final-date request in isolation.
- Once all required information is present, subject collection completes and the final-date lookup runs.
- A successful query clears stale subject state.
- A later final-date request may replace the previous subject.
- Ambiguity must preserve enough context for clarification.

## 11. Semantic boundaries

### Final dates versus partial dates

References to a final exam, final, mesa, or exam table belong to this capability. Explicit references to a partial exam belong to the partial-date capability.

Generic wording such as “when is the exam?” or “exam date” is semantically ambiguous unless conversation context or product terminology establishes whether it means a final or partial.

### Final dates versus registration

Asking when an exam table occurs is a date query. Asking to enroll, register, or sign up is an exam-registration request and must not be treated as a date-only consultation.

### Subject-only replies

A standalone subject does not independently express a final-date goal. It continues this capability only when the active flow is waiting for `materia`.

## 12. Representative examples

```text
When is the Física II exam table?
When can I take the Álgebra y Geometría Analítica final?
What final dates are available for Redes de Computadoras II?
```

Missing subject:

```text
User: When are the final exams?
Assistant: Which subject do you want to check?
User: Física II
```

Multiple results:

```text
Física I
→ cod1001, 2025-08-10
→ cod1003, 2025-08-25
```
