# Personal Attendance Capability — Acceptance Criteria

These acceptance criteria translate the behavioral requirements in `spec.md` into explicit, testable scenarios. They define observable outcomes without prescribing how the capability is implemented.

## AC-01 — Personal attendance with subject

**Given** the student asks about their own attendance and includes a subject  
**When** the request is processed  
**Then**:

- The request is interpreted as personal attendance.
- The request is identified as `consultar_asistencia`.
- The included subject is identified as `materia`.
- The assistant does not ask for the subject again.
- Once external prerequisites required by the current system are satisfied, the personal-attendance query can continue for the requested subject.

Representative example:

> ¿Cuántas faltas tengo en Física?

Expected interpretation:

- Intent: `consultar_asistencia`
- `materia`: `Física`

## AC-02 — Absence-oriented personal language

**Given** the student asks about their own attendance using absence-oriented language  
**When** the request is processed  
**Then** the request is interpreted as the same personal-attendance goal represented by `consultar_asistencia`.

Representative absence-oriented concepts include:

- faltas
- ausencias
- inasistencias
- falté
- no fui
- clases faltadas

These expressions are representative examples and do not define an exhaustive vocabulary list.

Representative scenarios:

| Request | Expected intent | Expected subject |
|---|---|---|
| “¿Cuántas faltas tengo en Física?” | `consultar_asistencia` | `Física` |
| “¿Cuántas veces falté a Física?” | `consultar_asistencia` | `Física` |
| “¿Cuántas ausencias tengo en Matemática?” | `consultar_asistencia` | `Matemática` |
| “Decime cuántas veces no fui a Física.” | `consultar_asistencia` | `Física` |
| “¿Cuántas clases faltadas tengo en Física?” | `consultar_asistencia` | `Física` |

## AC-03 — Attendance-oriented personal language

**Given** the student asks about their own attendance using attendance-oriented language  
**When** the request is processed  
**Then** the request is interpreted as `consultar_asistencia`.

Representative attendance-oriented concepts include:

- asistencia
- porcentaje de asistencia
- clases asistidas

Representative scenarios:

| Request | Expected intent | Expected subject |
|---|---|---|
| “¿Cómo estoy de asistencia en Física?” | `consultar_asistencia` | `Física` |
| “¿Qué porcentaje de asistencia tengo en Física?” | `consultar_asistencia` | `Física` |
| “¿Cuántas clases asistí en Física?” | `consultar_asistencia` | `Física` |

## AC-04 — General attendance policy

**Given** a user asks about institutional attendance requirements, allowed absences, minimum attendance, or attendance rules for maintaining academic standing  
**When** the request is processed  
**Then**:

- The request is interpreted as general attendance policy.
- The request is identified as `informar_asistencia`.
- The assistant provides general institutional policy information.
- The assistant does not enter the student's personal-attendance flow.
- The assistant does not request `materia` solely to answer the policy question.

Representative example:

> ¿Cuántas faltas puedo tener?

Expected intent:

`informar_asistencia`

Additional representative scenarios:

| Request | Expected intent |
|---|---|
| “¿Cuál es el porcentaje mínimo de asistencia?” | `informar_asistencia` |
| “¿Qué asistencia necesito para regularizar?” | `informar_asistencia` |
| “¿Cuál es la política de asistencia de la institución?” | `informar_asistencia` |

## AC-05 — Personal versus policy semantic boundary

**Given** two requests use the word “faltas”  
**When** one asks about the student's own record and the other asks about the permitted institutional limit  
**Then** the requests are distinguished by the user's goal rather than by the shared keyword.

| Request | User goal | Expected intent |
|---|---|---|
| “¿Cuántas faltas tengo?” | Consult the student's own attendance | `consultar_asistencia` |
| “¿Cuántas faltas puedo tener?” | Learn the institution's allowed-absence policy | `informar_asistencia` |

The first request may require a subject follow-up. The second must not request a subject solely to provide the policy answer.

## AC-06 — Missing subject

**Given** a personal-attendance request does not include a subject  
**When** the request is processed  
**Then**:

- It is still recognized as a personal-attendance request.
- It is identified as `consultar_asistencia`.
- The assistant asks the student to provide `materia`.
- The request remains pending so it can continue after the subject is provided.

Representative example:

> ¿Cuántas faltas tengo?

Expected outcome:

- Intent: `consultar_asistencia`
- `materia`: missing
- Assistant response: asks which subject the student wants to consult

## AC-07 — Subject follow-up

**Given** the assistant requested the missing subject for an active personal-attendance request  
**When** the student replies only with a subject, such as “Física”  
**Then**:

- The reply is identified as `materia` with the value `Física`.
- The original personal-attendance request continues.
- The student is not required to repeat the original request.
- An unrelated capability is not started.

## AC-08 — Successful attendance response

**Given** a personal-attendance request has a subject and all external prerequisites required by the current system are satisfied  
**When** attendance information is successfully returned  
**Then** the response includes values for:

- attended classes
- absent classes
- total classes
- attendance percentage

The four values must refer to the same requested subject and attendance record. The total must be consistent with the attended and absent counts, and the reported percentage must be consistent with those values.

## AC-09 — Subject replacement

**Given** a previous personal-attendance query used `Física`  
**When** a new personal-attendance request refers to `Matemática`  
**Then**:

- `Matemática` is identified as the current `materia`.
- `Matemática` replaces `Física` for the new query.
- Stale `Física` context does not determine the new response.
- Any returned attendance information belongs to `Matemática`, not `Física`.

Representative sequence:

1. “¿Cuántas faltas tengo en Física?”
2. “¿Y en Matemática?”

Expected current subject after the second request: `Matemática`.

## AC-10 — Language robustness

**Given** a personal-attendance request expresses a supported user goal and subject using a representative language variation  
**When** the request is processed  
**Then** the personal-attendance goal and subject are identified consistently.

The representative variations include:

- Uppercase and lowercase subject names.
- Accented and unaccented forms.
- The subject at the beginning or end of the sentence.
- Short or telegraphic phrasing.
- Multiword subjects supported by the project's subject catalog.

Representative scenarios:

| Variation | Request | Expected intent | Expected subject |
|---|---|---|---|
| Title case and accent | “¿Cuántas faltas tengo en Física?” | `consultar_asistencia` | `Física` |
| Lowercase and no accent | “faltas de fisica” | `consultar_asistencia` | `fisica` |
| Subject first | “Física: ¿cuántas ausencias tengo?” | `consultar_asistencia` | `Física` |
| Subject last | “¿Cómo estoy de asistencia en Matemática?” | `consultar_asistencia` | `Matemática` |
| Telegraphic | “asistencia física” | `consultar_asistencia` | `física` |
| Multiword subject | “¿Cuántas faltas tengo en Redes de Computadoras 1?” | `consultar_asistencia` | `Redes de Computadoras 1` |
| No subject | “¿Qué porcentaje de asistencia tengo?” | `consultar_asistencia` | Missing; assistant asks for it |

## AC-11 — Subject normalization and canonical resolution

**Given** a personal-attendance request contains a recognizable subject expression  
**When** that expression is resolved to a subject  
**Then**:

- The words supplied by the user are identified as the `materia` input independently from determining which catalog subject they represent.
- The resolved subject uses the canonical name defined by the authoritative subject catalog.
- Case and accent variations resolve to the same canonical subject when they identify the same catalog subject.
- Arabic and Roman numbering variants for the same level resolve to the same canonical subject.
- No canonical subject name is invented solely from the user's wording.

Representative scenarios:

| User expression | Expected behavior |
|---|---|
| `Física`, `física`, or `fisica` | Resolve using the catalog's canonical subject and the numbered-family default defined in AC-13. |
| `Física 1`, `Física I`, or `fisica i` | Resolve to canonical `Física I` when `Física I` exists in the catalog. |
| `Física 2` or `Física II` | Resolve to canonical `Física II` when `Física II` exists in the catalog. |

Recognition of the user's language and resolution to a canonical catalog subject must remain conceptually separate outcomes.

## AC-12 — Ambiguity handling and distinct subjects

**Given** a personal-attendance request contains a subject expression that can match multiple valid subjects in the authoritative subject catalog after applying the normalization and defaulting rules  
**When** the subject is resolved  
**Then**:

- The assistant does not choose one of the matching subjects arbitrarily.
- The assistant asks the student to clarify which valid subject they mean.
- The personal-attendance query does not continue with attendance information until one subject is resolved unambiguously.
- After clarification, the original personal-attendance request continues with the selected canonical subject.

**Given** the authoritative subject catalog contains similar but distinct subjects  
**When** a subject expression is resolved  
**Then** those subjects remain separate and are never merged.

Representative distinction:

- `Física I` and `Física II` are different subjects and must remain different canonical subjects.
- An expression that remains ambiguous must trigger clarification; the intentional unnumbered-to-level-I default in AC-13 is not ambiguous merely because other numbered levels exist.

## AC-13 — Numbered subject defaulting and equivalence

**Given** the authoritative subject catalog contains a numbered subject family  
**When** the student supplies an unnumbered, case-variant, accent-variant, Arabic-numbered, or Roman-numbered expression  
**Then**:

- An unnumbered expression resolves to level I when level I exists.
- Arabic and Roman numerals for the same level resolve to that level's canonical catalog subject.
- The canonical result uses the catalog subject identifier and display name.
- Different numbered levels are never merged.
- A number without a corresponding catalog subject does not create a new subject and instead follows the existing not-found or clarification behavior.

Representative scenarios:

| User expression | Catalog subjects | Expected result |
|---|---|---|
| `Física` or `fisica` | `Física I`, `Física II` | `Física I`; no clarification solely due to numbered levels |
| `Física 1`, `Física I`, or `fisica i` | `Física I`, `Física II` | Canonical `Física I` |
| `Física 2` or `Física II` | `Física I`, `Física II` | Canonical `Física II` |
| `Física 3` or `Física III` | `Física I`, `Física II`, `Física III` | Canonical `Física III` |
| `Álgebra` or `algebra` | `Álgebra I`, `Álgebra II` | `Álgebra I` |
| `Física 4` | `Física I`, `Física II`, `Física III` | No invented `Física IV`; not-found or clarification behavior |

## Scope boundary

These acceptance criteria do not redefine authentication, matrícula resolution, or the academic period used for attendance. Those concerns remain external prerequisites or constraints and retain their existing behavior.

## Traceability

| Acceptance Criterion | Specification Section |
|---|---|
| AC-01 — Personal attendance with subject | `Terminology and intent boundary`; `Capability input`; `Expected behavior` → `Personal attendance request with a subject` |
| AC-02 — Absence-oriented personal language | `Terminology and intent boundary`; `Examples` → `Personal attendance — consultar_asistencia`; `Acceptance criteria` item 1 |
| AC-03 — Attendance-oriented personal language | `Terminology and intent boundary`; `Examples` → `Personal attendance — consultar_asistencia`; `Acceptance criteria` item 1 |
| AC-04 — General attendance policy | `Terminology and intent boundary`; `Expected behavior` → `General attendance-policy request`; `Examples` → `General attendance policy — informar_asistencia`; `Acceptance criteria` item 7 |
| AC-05 — Personal versus policy semantic boundary | `Purpose`; `Terminology and intent boundary`; `Examples`; `Acceptance criteria` item 2 |
| AC-06 — Missing subject | `Capability input`; `Expected behavior` → `Personal attendance request without a subject`; `Examples` → `Personal attendance — consultar_asistencia`; `Acceptance criteria` item 4 |
| AC-07 — Subject follow-up | `Capability input`; `Expected behavior` → `Personal attendance request without a subject`; `Acceptance criteria` item 4 |
| AC-08 — Successful attendance response | `Expected behavior` → `Successful response`; `Acceptance criteria` item 5 |
| AC-09 — Subject replacement | `Capability input`; `Expected behavior` → `Repeated request with a different subject`; `Acceptance criteria` item 6 |
| AC-10 — Language robustness | `Terminology and intent boundary`; `Capability input`; `Examples` → `Personal attendance — consultar_asistencia`; `Acceptance criteria` items 1 and 3 |
| AC-11 — Subject normalization and canonical resolution | `Capability input` → `Subject recognition and canonical resolution`; `Acceptance criteria` items 8 and 9 |
| AC-12 — Ambiguity handling and distinct subjects | `Capability input` → `Subject recognition and canonical resolution`; `Expected behavior` → `Ambiguous subject`; `Acceptance criteria` item 12 |
| AC-13 — Numbered subject defaulting and equivalence | `Capability input` → `Subject recognition and canonical resolution`; `Acceptance criteria` items 8–11 |
