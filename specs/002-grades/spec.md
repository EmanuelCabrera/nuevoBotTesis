# Grades Capability Specification

## Purpose

This capability allows a student to ask for their own recorded grades for a
specific subject. It keeps the grades request focused on records supported by
the current academic data model and does not invent additional academic
meaning.

## Terminology and intent boundary

- `consultar_notas` represents a student asking for their own recorded grades
  or qualifications.
- A subject supplied while an existing grades request is waiting for `materia`
  is handled through the generic `proporcionar_materia` intent in the active
  grades context.
- A grades request is personal: it concerns the authenticated student's own
  records, not institutional grading policy or teacher/administrator actions.
- Expressions such as `notas`, `calificaciones`, `qué nota tengo`, and `cuánto
  saqué` may express the same personal-grades goal when the surrounding request
  concerns the student's own records.
- The supported language examples are representative and are not an exhaustive
  vocabulary list.

The following meanings are not assumed by this capability unless the current
backend contract explicitly supports them:

- average or cumulative average;
- passed or failed status;
- promotion or regularity status;
- final grade semantics;
- partial, recovery, or other exam-type semantics;
- any academic-period interpretation.

## Capability input and prerequisites

`materia` is the capability-specific conversational input and identifies the
subject whose recorded grades the student wants to consult.

- A subject may be included in the initial request.
- If the subject is missing, the assistant asks the student to provide it.
- After the subject is supplied, the original grades request continues.
- A subject supplied in a new grades request replaces any stale subject from an
  earlier request.
- Existing authentication and matrícula prerequisites remain unchanged and are
  treated as external prerequisites for this capability.

## Subject recognition and canonical resolution

Recognizing a subject expression and resolving it to an authoritative subject
are separate responsibilities:

- Subject recognition identifies the user-provided words as the `materia`
  input.
- Canonical resolution uses `SubjectCatalogRepository` and `SubjectResolver`
  against the authoritative subject catalog.
- The resolved result preserves the catalog subject identifier (`codigo`) and
  canonical display name (`nombre`).
- Case and accent differences are normalized according to the shared resolver
  contract.
- Arabic and Roman numbering variants for the same level are equivalent.
- An unnumbered expression for a numbered subject family defaults to level I
  when that catalog subject exists.
- Different numbered subjects remain distinct.
- A number that does not exist in the catalog does not create a subject.
- If valid ambiguity remains after normalization and defaulting, the assistant
  asks the student to clarify rather than selecting a subject arbitrarily.
- Grade records are queried only after the subject is resolved unambiguously.

Representative resolution examples:

| User expression | Expected canonical result when present in the catalog |
|---|---|
| `fisica` | `Física I` |
| `fisica 1` | `Física I` |
| `fisica 2` | `Física II` |
| `fisica ii` | `Física II` |
| `algebra` | `Álgebra I` |

## Supported grade-record semantics

The current implementation reads the following fields from a grade record:

- `nota`: the recorded grade value;
- `descripcion`: the record description;
- `created_at`: the record date or timestamp.

A returned grade record may expose those values. The capability must preserve
the values supported by the backend and must not infer unsupported academic
meaning from them.

- All grade records currently supported by the backend for the resolved subject
  are returned individually.
- Multiple records for one subject are not collapsed into an invented average.
- Ordering is unspecified unless the backend contract establishes that
  `created_at` is reliable enough to define chronological ordering.
- The current numeric `/10` formatting and color thresholds are legacy
  presentation behavior, not mandatory specification requirements.

## Expected behavior

### Personal grades request with a subject

Given that a student asks for their own grades and includes a valid subject:

1. The request is understood as `consultar_notas`.
2. The subject is identified as `materia`.
3. The subject is resolved to its canonical catalog identity.
4. The assistant does not ask for the subject again.
5. Once existing authentication and matrícula prerequisites are satisfied, the
   assistant returns the supported grade records for that subject.

### Personal grades request without a subject

Given that a student asks for their own grades without including a subject:

1. The request is understood as `consultar_notas`.
2. The assistant asks the student to provide `materia`.
3. The original grades request remains active.
4. After an unambiguous subject is supplied, the grades lookup continues.

### Subject not found

Given that the supplied subject expression does not resolve to a catalog
subject:

1. The assistant reports that the subject was not found.
2. The outcome is distinct from a valid subject with no grade records.
3. No grade query is performed for an invented or fabricated subject.

### Ambiguous subject

Given that the subject expression matches more than one valid catalog subject
after applying shared normalization and defaulting rules:

1. The assistant asks the student to clarify the intended subject.
2. No grade query is performed while the subject remains ambiguous.
3. After an unambiguous clarification, the original grades request continues.

### No grades

Given that the subject resolves canonically but the student has no grade
records for it:

1. The assistant reports that no grades were found for that subject.
2. The response does not report this as a subject-not-found error.

### Repeated request with a different subject

Given that a student has queried grades for one subject and then requests
grades for another:

1. The new subject becomes the current `materia`.
2. The previous subject does not determine the new query.
3. Returned records belong to the newly requested subject.

## Examples

### Personal grades — `consultar_notas`

Representative examples include:

- “Quiero ver mis notas.”
- “¿Cuáles son mis calificaciones?”
- “¿Cuánto saqué en Física?”
- “¿Qué nota tengo en Física?”
- “Necesito consultar mis notas de Matemática.”

These examples represent requests for the student's recorded grade results.

The following meanings require an explicit product decision or backend
evidence before being included as guaranteed grades behavior:

- “¿Cuál es mi promedio?”
- “¿Aprobé Física?”
- “¿Cómo me fue?”
- “¿Cuál fue el resultado del parcial?”
- “¿Cuál es mi nota final?”

## Out of scope

This specification does not redesign or introduce:

- authentication;
- matrícula resolution;
- academic-period selection or redesign;
- teacher or administrator grade management;
- creating, editing, or deleting grades;
- Supabase schema changes;
- invented averages;
- invented pass/fail, promotion, or regularity semantics;
- invented exam-type or partial-number semantics.
