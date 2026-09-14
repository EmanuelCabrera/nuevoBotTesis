# 004 — Final Exam Dates — Acceptance Criteria

## AC-01 — Explicit request with subject

**Given** an authenticated user asks for final-exam dates and includes a valid subject

**When** the request is processed

**Then** the final-date capability is selected, the subject is resolved, the subject is not requested again, and the lookup continues.

## AC-02 — Mesa and final wording

**Given** the user asks when a final, final exam, mesa, or exam table takes place

**When** the language is interpreted

**Then** it is recognized as a final-exam-date request.

## AC-03 — Missing subject

**Given** a final-date request does not identify a subject

**When** the flow starts

**Then** the assistant requests `materia` and preserves the final-date flow.

## AC-04 — Contextual subject follow-up

**Given** the active final-date flow requested a subject

**When** the user replies only with a subject

**Then** `materia` is captured, the same flow continues, collection completes, and the final-date action runs.

## AC-05 — Canonical subject resolution

**Given** a subject expression matches the authoritative catalog

**When** it is resolved

**Then** the canonical `Materia.codigo` and display name are preserved and used by the mesa lookup.

## AC-06 — Numbered subject variants

**Given** the catalog contains a numbered subject family

**When** the user supplies accent/case variants, Arabic/Roman numbering, or an unnumbered family name

**Then** the shared resolution rules apply, distinct levels remain distinct, and nonexistent levels are not invented.

## AC-07 — Invalid subject

**Given** no catalog subject matches the expression

**When** the request is processed

**Then** subject-not-found is reported and `MesaExamen` is not queried.

## AC-08 — Ambiguous subject

**Given** more than one catalog subject remains valid after normalization

**When** resolution is attempted

**Then** no first result is selected, no mesa query runs, and clarification is requested.

## AC-09 — Valid subject without mesas

**Given** the canonical subject exists but has no `MesaExamen` records

**When** the lookup runs

**Then** the assistant reports that no mesas are registered and does not report subject-not-found.

## AC-10 — One mesa

**Given** one mesa exists for the canonical subject

**When** the result is returned

**Then** its authoritative code and date are included.

## AC-11 — Multiple mesas

**Given** multiple mesas exist for the canonical subject

**When** the result is returned

**Then** every mesa code and date is included without silently dropping records.

## AC-12 — Canonical subject name

**Given** a subject resolves successfully

**When** the response is built

**Then** it identifies the subject using its canonical catalog display name.

## AC-13 — Repeated query and subject replacement

**Given** a completed query used Física I

**When** the user makes a new final-date request for Física II

**Then** Física II becomes current and stale Física I state does not determine the result.

## AC-14 — Backend failure

**Given** catalog or mesa access fails

**When** the request is processed

**Then** a controlled error is returned and no subject, code, date, or no-results outcome is fabricated.

## AC-15 — Final dates versus partial dates

**Given** one request explicitly concerns a final or mesa and another explicitly concerns a partial

**When** each is interpreted

**Then** the final request selects the final-date capability and the partial request selects the partial-date capability.

## AC-16 — Final dates versus registration

**Given** one request asks when a mesa occurs and another asks to enroll in it

**When** each is interpreted

**Then** only the first is a final-date consultation and the second selects exam registration.

## AC-17 — Subject-only language is contextual

**Given** a message contains only a subject expression

**When** it is interpreted without final-date context

**Then** it is not treated as an explicit final-date request; when the final-date flow is actively requesting `materia`, it continues that flow.

## AC-18 — Authentication prerequisite

**Given** the user is not authenticated

**When** the final-date action is reached

**Then** the inherited authentication requirement is enforced and no mesa data is returned.

## Traceability

| Criterion | Specification section |
|---|---|
| AC-01 | 2. Scope; 7. Main flows |
| AC-02 | 2. Scope; 11. Semantic boundaries |
| AC-03 | 7. Main flows; 10. Form and state behavior |
| AC-04 | 7. Main flows; 10. Form and state behavior |
| AC-05 | 5. Subject resolution; 6. Database contract |
| AC-06 | 5. Subject resolution |
| AC-07 | 9. Alternative and error flows |
| AC-08 | 5. Subject resolution; 9. Alternative and error flows |
| AC-09 | 9. Alternative and error flows |
| AC-10 | 6. Database contract; 8. Multiple mesas |
| AC-11 | 8. Multiple mesas |
| AC-12 | 5. Subject resolution |
| AC-13 | 10. Form and state behavior |
| AC-14 | 9. Alternative and error flows |
| AC-15 | 11. Semantic boundaries |
| AC-16 | 3. Out of scope; 11. Semantic boundaries |
| AC-17 | 10. Form and state behavior; 11. Semantic boundaries |
| AC-18 | 4. Authentication |
