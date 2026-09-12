# 003 — Acceptance Criteria

These criteria translate `spec.md` into testable behavior. They are not marked as passing until the baseline and verification stages.

## AC-01 — Explicit requirements request with subject

**Given** the user requests the requirements or correlatives of a valid subject

**When** the request is processed

**Then** the request is interpreted as a curricular-requirements query, the subject is identified and canonically resolved, and the query continues without asking for the subject again.

## AC-02 — Requirements and correlative language

**Given** the user uses language such as “what do I need to take”, “requirements”, “prerequisites”, “correlatives”, or “subjects I must have” for a specific subject

**When** the request is interpreted

**Then** it is treated as a requirements/correlatives query for that subject.

## AC-03 — Request without a subject

**Given** the user asks about subject requirements without naming a subject

**When** the request is processed

**Then** the assistant recognizes the requirements request, asks for the subject, and preserves the original requirements flow.

## AC-04 — Subject follow-up

**Given** the assistant asked for the missing subject

**When** the user replies only “Física II”

**Then** the subject is identified and canonically resolved, the original requirements query continues, no unrelated capability starts, and the user is not asked to repeat the original question.

## AC-05 — Canonical subject resolution

**Given** the user expresses a subject with writing variations

**When** it is matched against the authoritative catalog

**Then** the result preserves the canonical `Materia` identifier and display name.

## AC-06 — Numbered subject variants

**Given** the catalog contains a numbered subject family

**When** the user uses case, accent, Arabic/Roman numbering, or an unnumbered expression

**Then** case and accents are ignored, equivalent Arabic/Roman levels resolve to the same subject, an unnumbered expression resolves to level I when available, distinct levels are not merged, and missing levels are not invented.

Examples: `fisica` → `Física I`; `fisica 2`/`fisica ii` → `Física II`; `fisica 4` → not found when level IV is absent.

## AC-07 — Invalid subject

**Given** the expression matches no catalog record

**When** the request is processed

**Then** the assistant reports subject-not-found and does not present it as “no requirements”.

## AC-08 — Ambiguous subject

**Given** the expression can match multiple valid subjects after allowed normalization

**When** resolution is attempted

**Then** the system does not select the first result, does not query `MateriaEquivalencia`, requests clarification, and preserves the requirements flow.

## AC-09 — Valid subject with no registered requirements

**Given** the subject exists in the catalog

**When** it has no direct `MateriaEquivalencia` rows

**Then** the assistant reports “no requirements registered” rather than subject-not-found.

## AC-10 — Multiple direct requirements

**Given** the subject has multiple direct relationships

**When** the result is produced

**Then** every related subject is returned without dropping any. For the observed data, Física II returns Física I and Álgebra y Geometría Analítica.

## AC-11 — Canonical names in the response

**Given** direct requirements are returned

**When** the response is built

**Then** the queried subject and every requirement use canonical names from `Materia`.

## AC-12 — Subject replacement

**Given** the user queried requirements for Física II

**When** the user makes a new request for Análisis Matemático II

**Then** Análisis Matemático II becomes the current subject, Física II does not determine the new response, and the new subject's relationships are queried.

## AC-13 — Backend failure

**Given** an error occurs while accessing the catalog or relationships

**When** the request is processed

**Then** a controlled error is shown, no subjects or requirements are fabricated, the error is not reported as not-found or no-requirements, and enough context is preserved for retry when appropriate.

## AC-14 — Boundary with enrollment requirements

**Given** the user asks about documents, admission, or institutional enrollment requirements

**When** the request is interpreted

**Then** it is treated as an administrative enrollment query, not as subject requirements, and a subject is not requested solely to answer it.

## AC-15 — Boundary with academic equivalences

**Given** the user asks whether subjects passed at another university or career are recognized

**When** the request is interpreted

**Then** it is treated as an academic-equivalence query, not as correlatives for taking a subject.

## AC-16 — Direct relationships only

**Given** direct relationships are registered for a subject

**When** the response is produced

**Then** only those direct relationships are returned; no transitive expansion, student-history lookup, approval or eligibility inference, or unsupported period/plan semantics are added.

## Traceability

| Criterion | `spec.md` section |
|---|---|
| AC-01 | 2. Scope; 7. Main flows |
| AC-02 | 2. Scope; 3. Terminology |
| AC-03 | 7. Main flows — Request without a subject |
| AC-04 | 7. Main flows — Subject continuation; 9. State and slots |
| AC-05 | 4. Data contract; 6. Subject resolution |
| AC-06 | 6. Subject resolution |
| AC-07 | 8. Alternative and error flows |
| AC-08 | 6. Subject resolution; 8. Alternative and error flows |
| AC-09 | 4. Data contract; 8. Alternative and error flows |
| AC-10 | 4. Data contract; 12. Examples |
| AC-11 | 4. Data contract; 6. Subject resolution |
| AC-12 | 9. State and slots; 12. Examples |
| AC-13 | 8. Alternative and error flows |
| AC-14 | 10. Semantic boundaries |
| AC-15 | 10. Semantic boundaries |
| AC-16 | 4. Data contract; 11. Out of scope |
