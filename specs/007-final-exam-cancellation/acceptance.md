# 007 — Final Exam Registration Cancellation — Acceptance Criteria

## AC-01 — Explicit cancellation request with subject

**Given** the user requests cancellation for a specific subject

**When** `cancelar_inscripcion_mesa_examen` is recognized

**Then** the cancellation flow collects the required matrícula and resolves the
subject for lookup.

## AC-02 — Request without subject

**Given** the user requests cancellation without a subject

**When** the cancellation flow starts

**Then** `cancelar_mesa_form` requests `materia` and preserves the flow.

## AC-03 — Subject follow-up during the active form

**Given** the form is requesting `materia`

**When** the user provides only a subject

**Then** generic `proporcionar_materia` fills the slot and the form continues.

## AC-04 — Canonical subject resolution

**Given** a canonical or numbered subject expression

**When** cancellation resolves the subject

**Then** the lookup uses the canonical `Materia.codigo`.

## AC-05 — Invalid subject

**Given** the subject does not exist

**When** cancellation runs

**Then** it reports subject-not-found and does not query exam tables.

## AC-06 — Ambiguous subject

**Given** the expression matches multiple subjects

**When** cancellation resolves it

**Then** it asks for clarification and does not choose an arbitrary first row.

## AC-07 — No active registration

**Given** the subject is valid but the student has no matching registration

**When** cancellation runs

**Then** it reports no active registration and does not claim success.

## AC-08 — Active registration exists

**Given** the student has a matching registration for a mesa of the subject

**When** cancellation runs

**Then** the registration is cancelled according to the persistence contract.

## AC-09 — Already-cancelled registration

**Given** a matching row has `baja=true`

**When** cancellation runs

**Then** behavior is characterized and no new active-registration policy is
invented.

## AC-10 — Multiple matching registrations

**Given** more than one matching registration exists for the subject

**When** cancellation runs

**Then** the current behavior is explicit about whether one or all rows are
affected.

## AC-11 — Successful cancellation persistence

**Given** a matching registration is found

**When** cancellation succeeds

**Then** persistence reflects cancellation and the user receives confirmation.

## AC-12 — Registration remains separate

**Given** the user asks to register rather than cancel

**When** the request is classified

**Then** it uses `inscribirse_mesa_examen`, not cancellation.

## AC-13 — Backend failure

**Given** a catalog, table, registration, or persistence query fails

**When** cancellation runs

**Then** it returns a controlled error and does not claim success.

## AC-14 — State cleanup

**Given** cancellation completes or no matching registration is found

**When** the action returns

**Then** transient cancellation state is not left as an accidental pending
operation.

## AC-15 — Cancellation versus final-date consultation

**Given** the user asks when a final or mesa occurs

**When** the message contains date-consultation wording without cancellation

**Then** it is classified as `consultar_fecha_mesas_examen_final`.

## AC-16 — Authentication and matrícula

**Given** authentication or matrícula is missing

**When** cancellation is requested

**Then** the inherited prerequisite flow is preserved and no cancellation is
claimed.

## AC-17 — Re-registration policy remains deferred

**Given** a cancelled row remains in `Inscripcion`

**When** a later registration is attempted

**Then** this capability does not require a new policy; capability 006's
current duplicate behavior remains documented as a separate product decision.
