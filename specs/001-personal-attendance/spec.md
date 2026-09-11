# Personal Attendance Capability Specification

## Purpose

This capability allows a student to ask about their own attendance for a specific subject while keeping personal attendance queries distinct from questions about the institution's general attendance policy.

## Terminology and intent boundary

- `consultar_asistencia` represents a student asking about their own attendance record.
- `informar_asistencia` represents a user asking about general institutional attendance requirements, limits, or policies.
- Personal attendance requests may refer to attendance using any of the following expressions:
  - asistencia
  - faltas
  - ausencias
  - inasistencias
  - clases asistidas
  - clases faltadas
  - porcentaje de asistencia
- These expressions represent the same personal-attendance goal when the user is asking about their own record.
- The distinction between personal attendance and general policy is based on the user's goal, not on the presence of a particular keyword.

## Capability input

`materia` is the capability-specific conversational input and identifies the subject whose attendance record the student wants to consult.

- When the user includes a subject in the request, that subject must be identified as `materia`.
- When the user does not include a subject, the assistant must ask which subject they want to consult.
- After the user provides the missing subject, the assistant must continue the same personal-attendance request.
- A subject supplied in a new personal-attendance request must replace any subject retained from an earlier request.

### Subject recognition and canonical resolution

Recognizing the subject expression in the user's language and resolving that expression to an authoritative subject are separate responsibilities:

- Subject recognition identifies the words the user supplied as the `materia` input.
- Canonical subject resolution determines which subject in the authoritative subject catalog those words represent.
- Differences in capitalization or accents may represent the same subject. For example, `Física`, `física`, and `fisica` may resolve to the same canonical subject when supported by the authoritative subject catalog.
- For numbered subject families, an unnumbered expression intentionally resolves to the first level when that level exists in the authoritative catalog. For example, `Física` and `fisica` resolve to `Física I`, and `Álgebra` and `algebra` resolve to `Álgebra I`.
- Arabic and Roman numbering variants for the same level are equivalent. For example, `Física 1`, `Física I`, and `fisica i` resolve to the catalog subject `Física I`; `Física 2` and `Física II` resolve to `Física II`; and `Física 3` and `Física III` resolve to `Física III`. The same rule applies generically to other numbered subject families.
- Canonical subject names must come from the authoritative subject catalog rather than being invented from the user's wording.
- Similar but distinct catalog subjects must remain distinct. For example, `Física I` and `Física II` must never be merged.
- The unnumbered-to-level-I rule is an intentional default, not an ambiguity case. Therefore, `Física` resolves directly to `Física I` when that catalog subject exists and must not trigger clarification solely because numbered levels also exist.
- If a user expression can represent more than one valid subject after applying the defined normalization and numbering rules, the assistant must ask the user to clarify which subject they mean instead of selecting one arbitrarily.
- If a supplied number does not correspond to a valid catalog subject, the resolver must not invent a subject; it returns subject-not-found or requests clarification according to the surrounding capability behavior.
- Attendance information must be requested only after the subject has been resolved unambiguously.

## Expected behavior

### Personal attendance request with a subject

Given that a student asks about their own attendance and includes a subject:

1. The request is understood as `consultar_asistencia`.
2. The included subject is identified as `materia`.
3. The assistant does not ask for the subject again.
4. Once any external prerequisites required by the current system are satisfied, the assistant obtains and returns the student's attendance information for the requested subject.

### Personal attendance request without a subject

Given that a student asks about their own attendance without including a subject:

1. The request is understood as `consultar_asistencia`.
2. The assistant asks the student to provide the subject.
3. When the student supplies the subject, it is identified as `materia`.
4. The assistant continues the original attendance request rather than starting an unrelated capability.

### Successful response

A successful personal-attendance response must report all of the following for the requested subject:

- attended classes
- absent classes
- total classes
- attendance percentage

The values must describe the same attendance record and be internally consistent.

### General attendance-policy request

Given that a user asks about institutional attendance requirements, permitted absences, or the attendance needed to maintain academic standing:

1. The request is understood as `informar_asistencia`.
2. The assistant provides general institutional policy information.
3. The assistant does not treat the request as a query about the student's personal attendance record.
4. The assistant does not ask for `materia` solely to answer the general policy question.

### Repeated request with a different subject

Given that a student completes or begins a personal-attendance query for one subject and then asks about another subject:

1. The new subject is identified as `materia`.
2. The new subject replaces the previous subject for the new query.
3. Attendance information for the earlier subject must not be presented as if it belonged to the new subject.

### Ambiguous subject

Given that a personal-attendance request contains a subject expression that can match multiple valid subjects in the authoritative subject catalog:

1. The expression is still recognized as the `materia` input.
2. The assistant asks the student to clarify which valid subject they mean.
3. The assistant does not select a subject arbitrarily.
4. The personal-attendance request continues after the student identifies one unambiguous catalog subject.

## Examples

### Personal attendance — `consultar_asistencia`

The following are personal-attendance requests:

- “¿Cuántas faltas tengo en Física?”
- “¿Cuántas veces falté a Física?”
- “¿Cuántas inasistencias tengo en Física?”
- “¿Cómo estoy de asistencia en Física?”
- “¿Qué porcentaje de asistencia tengo en Física?”
- “¿Cuántas clases asistí en Física?”
- “¿Cuántas clases falté en Física?”
- “Quiero consultar mi asistencia en Redes de Computadoras 1.”
- “¿Cuántas faltas tengo?”

In the final example, the personal-attendance goal is clear but `materia` is missing, so the assistant must ask for it.

### General attendance policy — `informar_asistencia`

The following are general policy requests:

- “¿Cuál es el porcentaje mínimo de asistencia?”
- “¿Cuántas faltas puedo tener?”
- “¿Qué asistencia necesito para regularizar?”
- “¿Cuál es la política de asistencia de la institución?”

These questions concern institutional requirements rather than an individual's attendance record.

## Acceptance criteria

1. Personal requests using any supported attendance expression are treated as the same user goal.
2. Personal requests are distinguished from general policy questions even when both use words such as “asistencia” or “faltas.”
3. A subject included anywhere in a personal request is identified as `materia`.
4. A missing subject results in a request for `materia` and the original attendance query continues after it is provided.
5. A successful response includes attended classes, absent classes, total classes, and attendance percentage.
6. A follow-up request for a different subject uses the new subject and does not reuse stale subject context.
7. General policy requests receive policy information and do not enter the personal-attendance flow.
8. Subject expressions are resolved to canonical names from the authoritative subject catalog while preserving distinctions between separate subjects.
9. Case, accent, and the defined Arabic/Roman numbering variations resolve to the same canonical subject where they identify the same catalog level.
10. An unnumbered expression for a numbered subject family defaults to level I when that catalog subject exists; this default is not treated as ambiguity.
11. A number that does not correspond to a valid catalog subject does not produce an invented subject.
12. Ambiguous subject expressions remaining after normalization and valid defaulting result in a clarification request rather than an arbitrary subject selection.

## Out of scope

This specification does not redefine or redesign:

- authentication
- matrícula resolution
- the academic period used to calculate attendance

Those concerns retain their existing behavior and are treated as external prerequisites or constraints for this capability.
