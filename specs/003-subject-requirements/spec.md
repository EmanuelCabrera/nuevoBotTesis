# 003 — Subject Requirements and Correlatives

## 1. Purpose

Define the expected behavior when a student asks which requirements or correlatives are needed to take a subject.

The capability reports direct curricular relationships registered for the queried subject.

## 2. Scope

The capability answers questions such as:

- What do I need to take Física II?
- What are the correlatives for Física II?
- Which subjects do I need before Análisis Matemático II?
- What requirements does Redes de Computadoras II have?

The query concerns curricular requirements/correlatives for taking a subject, not the student's individual academic status.

## 3. Terminology

- **Queried subject**: the subject the user asks about.
- **Direct requirement or correlative**: a related subject recorded as required for the queried subject.
- **Authoritative catalog**: the `Materia` catalog, which provides each subject's canonical code and display name.
- **Curricular relationship**: a row in `MateriaEquivalencia`.

In this capability, “equivalencia” is the table's historical technical name; it does not mean that subjects are academically interchangeable.

## 4. Data contract

Each relationship is interpreted as follows:

```text
MateriaEquivalencia.materia_codigo = queried subject
MateriaEquivalencia.equivalencia_codigo = direct requirement/correlative
```

Displayed names must come from `Materia` and preserve canonical identity (code and display name).

Confirmed example:

```text
Física II
→ Física I
→ Álgebra y Geometría Analítica
```

The capability returns only registered direct relationships. It does not expand transitive chains.

## 5. Preconditions and inherited legacy behavior

The current implementation requires authentication and matrícula before executing the query. These are inherited system preconditions and remain in scope for now.

Curricular requirements are not matrícula-specific data. Authentication and matrícula redesign are out of scope.

## 6. Subject resolution

The user's subject expression must be resolved against the authoritative catalog using the shared rules established by previous capabilities:

- ignore case differences;
- ignore accent differences;
- treat Arabic and Roman numbering as equivalent when they identify the same catalog level;
- resolve an unnumbered expression to level I of a numbered family when that level exists;
- preserve the catalog's canonical code and display name;
- do not invent subjects or levels;
- detect ambiguous expressions and request clarification;
- never select the first match arbitrarily.

Examples:

```text
fisica                  → Física I
fisica 2                → Física II
fisica ii               → Física II
analisis matematico 2   → Análisis Matemático II
algoritmos 1            → Algoritmos y Estructuras I
unknown subject         → subject not found
ambiguous expression    → request clarification
```

Language recognition and canonical subject resolution are conceptually separate stages.

## 7. Main flows

### Request with a subject

1. The user expresses a requirements/correlatives request.
2. The queried subject is identified.
3. The subject is resolved to its canonical catalog record.
4. Its direct relationships are queried.
5. All registered correlatives are returned with canonical names.

### Request without a subject

1. The user asks about requirements without naming a subject.
2. The assistant asks for the subject.
3. The original requirements flow is preserved.

### Subject continuation

1. The assistant requested the missing subject.
2. The user replies with a subject expression, such as “Física II”.
3. The subject is resolved canonically.
4. The original requirements request continues without requiring the user to repeat it.

## 8. Alternative and error flows

- **Subject not found**: report that the subject does not exist in the catalog; do not present it as a subject with no requirements.
- **Ambiguous subject**: request clarification; do not query `MateriaEquivalencia` yet.
- **Valid subject with no relationships**: report that no requirements are registered for that subject, without inferring requirements outside the available data.
- **Backend error**: provide a controlled error; do not represent it as subject-not-found or no-requirements, and preserve enough context to retry when possible.

## 9. State and slots

- `materia` represents the current subject expression and must be replaceable by a later query.
- Flow context must be preserved while the subject or clarification is pending.
- A successful query must not leave stale subject state that contaminates a later query.
- Resolution and response must use the same canonical record.

## 10. Semantic boundaries

This capability covers curricular requirements/correlatives for taking a subject.

It must not be confused with:

- institutional admission or administrative enrollment requirements;
- exam-table registration;
- recognition of subjects passed at another institution;
- grades or marks;
- attendance;
- general subject information.

## 11. Out of scope

- authentication redesign;
- matrícula redesign;
- checking whether the student personally passed a correlative;
- querying `Notas` or `MateriaCursada` to determine eligibility;
- inferring pass/fail, regularity, or promotion;
- automatic enrollment;
- modifying requirements or subjects;
- recursive or transitive prerequisite expansion;
- academic-period logic;
- study-plan versions;
- assessment-type interpretation;
- interchangeable academic equivalences.

## 12. Examples

### Result with multiple correlatives

```text
User: What do I need to take Física II?

Expected response:
- Física I
- Álgebra y Geometría Analítica
```

### Missing subject

```text
User: What requirements do I need to take a subject?
Assistant: Which subject's requirements do you want to check?
User: Física II
```

The second message continues the original request.

### Valid subject with no relationships

```text
The subject exists but has no direct rows:
→ report “no requirements registered”
```

### Unknown subject

```text
User: What requirements does a subject that does not exist have?
→ report “subject not found”
```
