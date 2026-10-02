# 006 — Final Exam Registration

## 1. Purpose

This capability allows an authenticated student to register for one available
final-exam table (`MesaExamen`) for a subject.

The flow is distinct from consulting final-exam dates and from cancelling an
existing registration.

## 2. Scope

The capability covers:

- an explicit request to register for a final exam;
- collecting the student's matrícula and subject when either is missing;
- resolving the subject against the canonical Materia catalog;
- listing the available exam tables for the subject;
- selecting one table by its code or date;
- preventing a duplicate registration for the same student and table;
- inserting a registration for the selected table;
- controlled invalid-subject, no-table, duplicate, and backend-error outcomes.

## 3. Terminology

- **Subject**: a canonical row in `Materia`.
- **Exam table / mesa**: a row in `MesaExamen` identified by `codigo` and
  associated with a subject through `materia_codigo`.
- **Registration**: a row in `Inscripcion` linking a student matrícula to one
  exam-table code.
- **Student**: the authenticated user identified by the matrícula used by the
  current product flow.

## 4. Data contract

The observed tables are:

### Materia

The subject catalog provides `codigo` and canonical `nombre`.

### MesaExamen

Observed columns:

- `codigo`
- `created_at`
- `fecha`
- `materia_codigo`
- `presidente`
- `primer_vocal`

`MesaExamen.materia_codigo` references `Materia.codigo`.

### Inscripcion

Observed columns:

- `id`
- `created_at`
- `codigo_mesa`
- `estudiante`
- `baja`
- `fecha_inscripcion`

`Inscripcion.codigo_mesa` is related to `MesaExamen.codigo`. The `estudiante`
column stores the matrícula used by the current application flow. The
available public data does not establish an additional student-specific
eligibility contract.

The current observed data contains 8 exam tables and 35 registration rows.
The database contains a `baja` field, but registration eligibility and
registration-period semantics are not defined by this capability.

## 5. Preconditions and inherited behavior

The current flow requires authentication and matrícula. These prerequisites
are inherited from the existing product architecture and are preserved in
006.

The capability does not redesign authentication or matrícula validation.

## 6. Subject resolution

Subject identity must use the shared canonical infrastructure:

`SubjectCatalogRepository` → `SubjectResolver` → canonical `Materia.codigo`.

The intended behavior includes accent/case normalization, Arabic/Roman
numbering variants, level-I defaulting where supported, explicit not-found
handling, and clarification for ambiguous expressions. Registration must not
select the first partial name match arbitrarily.

## 7. Registration flow

The intended conversation is:

1. `inscribirse_mesa_examen` starts `inscripcion_mesa_form`.
2. The form collects `matricula` and `materia`.
3. A valid subject is resolved to its canonical code.
4. Available `MesaExamen` rows for that code are listed.
5. `seleccionar_mesa_form` collects a table `fecha` or `codigo`.
6. The selected table is validated.
7. A duplicate registration is checked for the same matrícula and table.
8. A new `Inscripcion` row is created when no duplicate exists.
9. Registration slots and active flow state are cleared after completion.

If multiple tables are available, the student must select one. If no table is
available, no registration is created.

## 8. Alternative and error flows

- Missing subject or matrícula: keep the registration flow active and ask for
  the missing value.
- Subject not found: report the invalid subject and do not list or register a
  table.
- Ambiguous subject: ask for clarification and do not query or register a
  table until resolved.
- No available tables: report that no table is available and do not create a
  registration.
- Invalid table code/date: report that the selected table does not exist.
- Existing registration: report the duplicate and do not insert another row.
- Backend failure: return a controlled error and avoid fabricating a
  registration result.

## 9. State and slots

The relevant slots are:

- `is_authenticated`
- `matricula`
- `materia`
- `codigo_mesa_examen`
- `fecha_mesa`
- `flujo_actual`

`inscripcion_mesa_form` requires `matricula` and `materia`.
`seleccionar_mesa_form` collects either a table code or date through the
current validation behavior.

After successful registration or a confirmed duplicate, the selected table,
subject, date, and registration flow should not remain stale. Retryable
subject/backend failures should preserve only the state necessary to continue
the current flow.

## 10. Semantic boundaries

Registration requests include actions such as “inscribirme”, “anotarme”,
“registrarme” or “reservar lugar” for a final/mesa. They are distinct from:

- final-date consultation (`consultar_fecha_mesas_examen_final`);
- partial-date consultation (`consultar_fechas_parciales`);
- cancellation (`cancelar_inscripcion_mesa_examen`);
- subject requirements;
- grades and attendance.

A subject-only reply is contextual while the registration form is requesting
`materia`; it is not an explicit registration request in isolation.

## 11. Out of scope

006 does not add or infer:

- prerequisite approval;
- grades, attendance, or `MateriaCursada` eligibility checks;
- registration deadlines or academic periods;
- exam capacity or availability status beyond existing rows;
- automatic selection of a table when the user has not selected one;
- cancellation behavior;
- post-completion elliptical follow-ups;
- schema changes or new student-specific semantics.
