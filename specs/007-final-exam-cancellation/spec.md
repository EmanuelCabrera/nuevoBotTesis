# 007 — Final Exam Registration Cancellation

## Purpose

This capability lets an authenticated student cancel an existing final-exam
registration for a subject. The current implementation operates on the
student's registrations associated with the exam tables of that subject.

## Scope

In scope:

- recognizing an explicit cancellation request;
- collecting matrícula and materia when either is missing;
- finding the exam tables associated with the requested subject;
- finding the student's registrations for those tables;
- cancelling matching registrations using the current persistence behavior;
- reporting success, no matching registration, invalid subject, and backend
  errors in a controlled way.

The capability does not select a new exam table, create a registration, or
change the registration policy used by capability 006.

## Terminology

- **Materia**: a canonical subject from `Materia`.
- **MesaExamen**: a final-exam table associated with a subject through
  `materia_codigo`.
- **Inscripcion**: a student's registration for a table through `codigo_mesa`.
- **Active registration**: the product concept intended by the cancellation
  flow. Under the inherited persistence contract, matching rows are deleted
  regardless of `baja`; redefining that policy remains out of scope.

## Preconditions and inherited behavior

The cancellation form requests `matricula` and `materia`. The action also
verifies `is_authenticated` before reading or mutating registration data. A
missing matrícula or subject keeps the cancellation flow pending so the form
can collect the missing value.

## Conversation flow

The intended current flow is:

```text
cancelar_inscripcion_mesa_examen
→ cancelar_mesa_form
→ requested_slot: matricula, then materia as needed
→ action_cancelar_inscripcion_mesa_examen
```

During an active form, a subject-only answer is represented by the generic
`proporcionar_materia` intent. Post-completion elliptical follow-ups are not
part of this capability.

## Data contract

The action uses these relationships:

```text
Materia.codigo
    ↑ MesaExamen.materia_codigo
MesaExamen.codigo
    ↑ Inscripcion.codigo_mesa
Inscripcion.estudiante = matrícula
```

The observed `Inscripcion` fields are `id`, `created_at`, `codigo_mesa`,
`estudiante`, `baja`, and `fecha_inscripcion`. The current action physically
deletes matching rows; it does not update `baja`, write a cancellation
timestamp, or change `fecha_inscripcion`.

## Cancellation behavior

The action:

1. obtains the canonical catalog through `SubjectCatalogRepository`;
2. resolves the subject through `SubjectResolver`;
3. queries every `MesaExamen.codigo` for the canonical `Materia.codigo`;
4. queries `Inscripcion` by matrícula and mesa code;
5. physically deletes each matching row under the existing persistence
   contract;
6. reports how many rows were deleted;
7. clears the subject and active flow after success, no registration, or no
   available table.

Invalid and ambiguous subjects clear the unresolved subject while keeping the
cancellation flow active for a retry. Backend failures retain the pending flow
and never claim cancellation success.

## Outcomes

- valid subject with matching registration: report cancellation success;
- valid subject without a matching registration: report that no active
  registration was found;
- subject not found: report the subject error without querying tables;
- ambiguous subject: request clarification before querying tables;
- backend failure: return a controlled error and do not claim cancellation.

## Semantic boundaries

Cancellation is distinct from:

- `inscribirse_mesa_examen`: creating a registration;
- `consultar_fecha_mesas_examen_final`: consulting dates;
- `consultar_fechas_parciales`: consulting partial dates;
- grades, attendance, and subject requirements.

Phrases such as “quiero cancelar”, “dar de baja”, “desanotame”, or “ya no voy
a rendir” belong to cancellation when they refer to a final-exam registration.

## Duplicate and re-registration policy

Capability 006 currently treats any existing `Inscripcion` row as blocking a
new registration, including rows with `baja=true`. Cancellation therefore has
a direct relationship with a deferred product decision: whether a cancelled
registration should permit re-registration. This capability does not decide or
change that policy.

## Out of scope

- post-completion contextual follow-ups;
- cancellation of partial exams;
- cancellation deadlines, fees, or eligibility rules;
- prerequisite, grade, attendance, or matrícula eligibility checks beyond the
  inherited flow;
- selection of a different mesa;
- redesign of the `baja` data model;
- allowing re-registration after cancellation;
- Supabase schema or data changes.
