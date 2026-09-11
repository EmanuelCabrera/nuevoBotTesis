# Grades Capability — Acceptance Criteria

These criteria derive from `spec.md` and define observable behavior without
prescribing implementation details.

## AC-01 — Personal grades request with subject

**Given** the student requests their own recorded grades and includes a valid
subject  
**When** the request is processed  
**Then**:

- The request is interpreted as personal grades.
- The request is identified as `consultar_notas`.
- The subject is identified as `materia`.
- The assistant does not ask for the subject again.
- After existing authentication and matrícula prerequisites are satisfied, the
  grades lookup can continue.

Representative example:

> ¿Cuánto saqué en Física?

Expected interpretation:

- Intent: `consultar_notas`
- `materia`: `Física`

## AC-02 — Personal grades language

**Given** the student asks for their own recorded grades using common grade or
qualification language  
**When** the request is processed  
**Then** the request is interpreted as `consultar_notas`.

Representative concepts include:

- notas;
- calificaciones;
- qué nota tengo;
- cuánto saqué.

Representative scenarios:

| Request | Expected intent |
|---|---|
| “Quiero ver mis notas.” | `consultar_notas` |
| “¿Cuáles son mis calificaciones?” | `consultar_notas` |
| “¿Qué nota tengo en Física?” | `consultar_notas` |
| “¿Cuánto saqué en Física?” | `consultar_notas` |

These are representative expressions, not an exhaustive vocabulary list.

## AC-03 — Missing subject

**Given** a personal grades request does not include a subject  
**When** the request is processed  
**Then**:

- It is still recognized as `consultar_notas`.
- The assistant asks the student to provide `materia`.
- The grades request remains active while the subject is missing.

Representative example:

> Quiero ver mis notas.

Expected outcome:

- Intent: `consultar_notas`
- `materia`: missing
- Assistant asks which subject the student wants to consult.

## AC-04 — Subject follow-up

**Given** the assistant requested the missing subject for an active grades
request  
**When** the student replies with a subject such as `Física`  
**Then**:

- The reply is identified as `materia`.
- The subject is resolved against the authoritative catalog.
- The original grades request continues.
- The student does not need to repeat the original grades question.
- An unrelated capability is not started.

## AC-05 — Canonical subject resolution

**Given** a grades request contains a recognizable subject expression  
**When** the subject is resolved  
**Then**:

- Resolution uses the shared `SubjectCatalogRepository` and `SubjectResolver`
  contract.
- The returned subject preserves the authoritative catalog `codigo`.
- The returned subject preserves the authoritative catalog `nombre`.
- The grade lookup uses the canonical subject identity.
- No canonical subject name is invented from the user's wording.

## AC-06 — Numbered subject variants

**Given** the authoritative catalog contains the relevant numbered subject
family  
**When** the student supplies equivalent subject expressions  
**Then**:

- Case differences are ignored.
- Accent differences are ignored.
- Arabic and Roman numerals for the same level are equivalent.
- An unnumbered family expression defaults to level I when level I exists.
- Different levels remain distinct.
- A nonexistent level is not invented.

Representative scenarios:

| User expression | Expected canonical result |
|---|---|
| `fisica` | `Física I` |
| `fisica 1` | `Física I` |
| `fisica 2` | `Física II` |
| `fisica ii` | `Física II` |
| `algebra` | `Álgebra I` |
| `fisica 4` | Not found; no invented subject |

## AC-07 — Invalid subject

**Given** the supplied subject expression does not resolve to a valid catalog
subject  
**When** the grades request is processed  
**Then**:

- The assistant reports a subject-not-found outcome.
- No invented subject is used.
- The result is not reported as “no grades” for a valid subject.
- The grades query is not executed for an unresolved subject.

## AC-08 — Ambiguous subject

**Given** a subject expression remains ambiguous after shared normalization and
valid defaulting  
**When** the grades request is processed  
**Then**:

- The assistant asks the student to clarify which subject they mean.
- The assistant does not choose one subject arbitrarily.
- The grades query does not execute while the subject remains ambiguous.
- After clarification with an unambiguous subject, the original grades request
  continues.

## AC-09 — No grades

**Given** the subject resolves to a valid canonical catalog subject  
**When** no grade records exist for the authenticated student and that subject
**Then**:

- The assistant reports a specific no-grades outcome.
- The response identifies the resolved subject where supported.
- The outcome is distinct from subject-not-found.

## AC-10 — Multiple grades

**Given** multiple grade records exist for the resolved subject  
**When** the grades request is processed  
**Then**:

- Every grade record currently supported by the backend is returned
  individually.
- Records are not silently collapsed into one invented average.
- The records all belong to the requested canonical subject.

Ordering is not required unless the backend contract establishes reliable
chronological ordering through `created_at`.

## AC-11 — Grade record consistency

**Given** grade records are returned by the current backend  
**When** the assistant presents them  
**Then**:

- The supported `nota` value is preserved.
- The supported `descripcion` value is preserved when present.
- The supported `created_at` value is preserved or presented as a date when
  the current contract allows it.
- The response does not invent averages, pass/fail status, promotion,
  regularity, exam types, or partial numbers.

Current `/10` formatting and color thresholds are legacy presentation details,
not mandatory acceptance requirements unless separately specified.

## AC-12 — Subject replacement

**Given** a previous grades request used `Física`  
**When** a new grades request refers to `Matemática`  
**Then**:

- `Matemática` becomes the current `materia`.
- Stale `Física` state does not determine the new query.
- Returned grade records belong to `Matemática`.

Representative sequence:

1. “¿Qué nota tengo en Física?”
2. “¿Y en Matemática?”

## AC-13 — Backend failure

**Given** the grades backend cannot be reached or returns an error  
**When** the grades request is processed  
**Then**:

- The assistant returns a controlled error response.
- No fabricated grade record is presented.
- The failure is not reported as a successful no-grades result.

## AC-14 — Scope boundary

**Given** the grades capability is implemented or exercised  
**Then** it must not introduce:

- authentication redesign;
- matrícula redesign;
- academic-period redesign;
- teacher or administrator grade management;
- grade creation or modification;
- Supabase schema changes;
- invented averages;
- invented pass/fail, promotion, or regularity semantics;
- invented exam-type or partial-number semantics.

## Traceability

| Acceptance Criterion | Specification Section |
|---|---|
| AC-01 — Personal grades request with subject | `Capability input and prerequisites`; `Expected behavior — Personal grades request with a subject` |
| AC-02 — Personal grades language | `Terminology and intent boundary`; `Examples — Personal grades` |
| AC-03 — Missing subject | `Capability input and prerequisites`; `Expected behavior — Personal grades request without a subject` |
| AC-04 — Subject follow-up | `Capability input and prerequisites`; `Expected behavior — Personal grades request without a subject` |
| AC-05 — Canonical subject resolution | `Subject recognition and canonical resolution` |
| AC-06 — Numbered subject variants | `Subject recognition and canonical resolution`; resolution examples |
| AC-07 — Invalid subject | `Expected behavior — Subject not found` |
| AC-08 — Ambiguous subject | `Subject recognition and canonical resolution`; `Expected behavior — Ambiguous subject` |
| AC-09 — No grades | `Expected behavior — No grades` |
| AC-10 — Multiple grades | `Supported grade-record semantics`; `Expected behavior — Personal grades request with a subject` |
| AC-11 — Grade record consistency | `Supported grade-record semantics`; scope of supported fields |
| AC-12 — Subject replacement | `Capability input and prerequisites`; `Expected behavior — Repeated request with a different subject` |
| AC-13 — Backend failure | `Expected behavior — Subject not found`; `Supported grade-record semantics` |
| AC-14 — Scope boundary | `Out of scope`; `Terminology and intent boundary` |

## Explicitly avoided assumptions

This acceptance document does not require or assume:

- a final average;
- a pass/fail result;
- promotion or regularity status;
- a grading scale beyond values currently returned by the backend;
- a partial, final, or recovery exam number;
- academic-period filtering;
- a reliable chronological order unless confirmed by the backend contract.
