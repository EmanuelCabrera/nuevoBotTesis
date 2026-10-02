# 006 — Final Exam Registration — Acceptance Criteria

## AC-01 — Explicit registration request with subject

**Given** the user is authenticated and provides a subject

**When** the user requests registration for a final exam

**Then** the registration flow starts and the subject is collected for table
lookup.

## AC-02 — Request without subject

**Given** the user requests registration without a subject

**When** `inscribirse_mesa_examen` is recognized

**Then** `inscripcion_mesa_form` asks for `materia` and preserves the flow.

## AC-03 — Subject follow-up during the active form

**Given** `inscripcion_mesa_form` is requesting `materia`

**When** the user supplies only a subject

**Then** the subject slot is filled and the registration flow continues.

## AC-04 — Canonical subject resolution

**Given** a subject expression such as `fisica 2` or `fisica ii`

**When** registration resolves the subject

**Then** it uses the canonical `Materia.codigo` for subsequent queries.

## AC-05 — Invalid subject

**Given** the subject does not exist in the catalog

**When** registration attempts subject resolution

**Then** it reports subject-not-found and does not list or register a table.

## AC-06 — Ambiguous subject

**Given** the expression matches multiple catalog subjects

**When** registration resolves the subject

**Then** it asks for clarification and does not select an arbitrary first row.

## AC-07 — No available exam tables

**Given** the subject is valid but has no `MesaExamen` rows

**When** the flow looks up available tables

**Then** it reports no available tables and creates no registration.

## AC-08 — One available exam table

**Given** exactly one table exists for the subject

**When** the user confirms that table by code or date

**Then** the selected table is validated and registration can be created.

## AC-09 — Multiple available exam tables

**Given** multiple tables exist for the subject

**When** the tables are offered

**Then** all direct options are shown and one table must be selected.

## AC-10 — Exam-table selection

**Given** a table code or date is supplied

**When** the selection form completes

**Then** the corresponding `MesaExamen.codigo` is validated before insertion.

## AC-11 — Successful registration

**Given** a valid student matrícula and selected table with no duplicate

**When** the registration action runs

**Then** one `Inscripcion` row is inserted with the matrícula, table code, and
registration timestamp.

## AC-12 — Duplicate registration

**Given** the same student is already registered for the selected table

**When** the registration action runs

**Then** it reports the duplicate and does not insert another row.

## AC-13 — Cancellation is separate

**Given** the user asks to cancel an existing registration

**When** the cancellation intent is recognized

**Then** the request uses the cancellation capability and is not treated as a
new registration.

## AC-14 — Backend failure

**Given** catalog, table, or registration persistence access fails

**When** the relevant action runs

**Then** it returns a controlled error and does not claim that registration
succeeded.

## AC-15 — State cleanup

**Given** registration succeeds or a duplicate is confirmed

**When** the flow completes

**Then** `materia`, table-selection slots, and `flujo_actual` do not retain
stale registration state.

## AC-16 — Registration versus date consultation

**Given** a user asks when a final/mesa occurs rather than asking to register

**When** the message contains date-consultation language

**Then** it is not classified as `inscribirse_mesa_examen`.

## AC-17 — Authentication and matrícula prerequisites

**Given** authentication or matrícula is missing

**When** registration is requested

**Then** the inherited prerequisite flow is preserved and no registration is
created.
