# 008 — Materias cursadas / Course Records — Specification

## Purpose

Capability 008 lets an authenticated student list the course records stored for
their matrícula.

In this capability, **materias cursadas** means:

> the `MateriaCursada` records associated with the student's matrícula.

It does not mean currently enrolled subjects, subjects currently being studied,
subjects from the current semester, approved subjects only, or the student's
complete curriculum. The observable database contract cannot represent those
meanings reliably.

## Request architecture

- Main intent: `consultar_materias`.
- Relevant entity: `matricula`.
- Required functional input: `matricula`.
- Authentication slot: `is_authenticated`.
- Form: `materias_form`.
- Form required slots: `matricula` only.
- Action: `action_consultar_materias`.
- Legacy flow marker: `flujo_actual=consultar_materias`.

The capability does not request a subject. The `materia` entity/slot and
`SubjectResolver` are not part of its contract.

## Supported requests

Explicit course-record requests include:

- “qué materias cursé”;
- “mostrame mis materias cursadas”;
- “qué materias figuran como cursadas”;
- “consultar mis materias cursadas”;
- equivalent requests containing a matrícula.

General wording such as “qué materias tengo” or “mostrame mis materias” remains
supported, but the response explicitly labels its data as registered course
records. The bare phrase “qué tengo” is not an accepted 008 request.

Unsupported meanings include:

- “en qué materias estoy inscripto”;
- “qué materias estoy cursando actualmente”;
- “mis materias del cuatrimestre”;
- “mis materias de este semestre”.

## Dialogue contract

1. Rasa recognizes `consultar_materias`.
2. If `matricula` is already set, the action can run directly.
3. Otherwise `materias_form` requests only `matricula`.
4. When the form completes, `action_consultar_materias` executes.
5. The action independently checks authentication and matrícula.

The legacy continuation rule based on
`flujo_actual=consultar_materias` remains in place. The form owns the normal
interaction, but removing shared continuation behavior is outside the smallest
safe 008 change.

## Database contract

### `MateriaCursada`

Observed columns:

- `id`;
- `created_at`;
- `fecha_cursada`;
- `aprobada`;
- `cod_materia`;
- `estudiante`.

The action filters `estudiante` by matrícula and uses the related
`Materia.nombre` as the canonical display name. The current key cannot inspect
the OpenAPI schema, so exact constraint names are not verified.

The database exposes no active-enrollment flag, cancellation flag, academic
period, semester, or academic-year field. `aprobada` is not a current-enrollment
indicator and is not filtered.

## Action query and output

```text
MateriaCursada
  .select("fecha_cursada, Materia(nombre)")
  .eq("estudiante", matricula)
```

The action:

- keeps every returned row and performs no deduplication;
- orders rows by `fecha_cursada` ascending, then canonical subject name;
- displays `Materia.nombre` and `fecha_cursada` for each record;
- reports the raw record count;
- explicitly calls the result “registros de materias cursadas”.

No filter is applied for current date, period, enrollment state, cancellation,
or approval.

## Result and cleanup behavior

- One or more rows: display the ordered records and clear `flujo_actual`.
- No rows: report that no course records were found and clear `flujo_actual`.
- Invalid/nonexistent matrícula: indistinguishable from a valid student with no
  course records under the current query contract.
- Authentication failure: do not query Supabase, explain the requirement, and
  clear `flujo_actual`.
- Backend failure: emit a controlled error and clear `flujo_actual`.
- Missing matrícula on direct action invocation: request it and retain
  `flujo_actual=consultar_materias` for the legacy continuation path.

The action never clears `materia`, because that slot is unrelated to this
capability. It keeps `matricula` available for a repeated explicit request.

## Semantic boundaries

- `consultar_notas`: grades, results, or scores.
- `consultar_asistencia`: absences or attendance.
- `consultar_requerimientos_materia`: prerequisites for a specific subject.
- final-exam registration/cancellation intents: change an exam registration.
- final/partial date intents: request examination dates.
- `proporcionar_materia`: supplies a subject to an active form.

“A qué finales estoy inscripto” does not mean `MateriaCursada` and is not
implemented as a list operation by capabilities 006/007.

## Explicit non-goals

- No `SubjectResolver` integration.
- No `materia` form input.
- No invented current-semester, active-enrollment, or historical-period filter.
- No approved-only or curriculum interpretation.
- No post-completion elliptical subject follow-up.
- No changes to capabilities 001–007.
