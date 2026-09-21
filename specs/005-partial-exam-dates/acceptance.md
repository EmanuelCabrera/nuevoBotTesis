# 005 — Partial Exam Dates — Acceptance Criteria

## AC-01 — Explicit partial-date request with subject

**Given** an authenticated user asks for partial dates and includes a valid
subject

**When** the request is processed

**Then** the partial-date capability is selected, the subject is not requested
again, and the lookup continues.

## AC-02 — Partial wording

**Given** the request explicitly mentions a parcial, parciales, or partial
evaluations

**When** the language is interpreted

**Then** it is recognized as a partial-date request rather than a final-date or
grades request.

## AC-03 — Missing subject activates collection

**Given** a partial-date request does not identify a subject

**When** the flow starts

**Then** `fechas_parciales_form` requests `materia` and preserves the
partial-date flow.

## AC-04 — Contextual subject follow-up

**Given** the active partial-date form is requesting `materia`

**When** the user replies with a subject-only expression

**Then** generic `proporcionar_materia` fills the slot, the form completes, and
the partial-date action runs.

## AC-05 — Canonical subject resolution

**Given** a subject expression matches one authoritative catalog subject

**When** it is resolved

**Then** the canonical `Materia.codigo` is used in the `Parciales` query and the
canonical display name is available for the response.

## AC-06 — Numbered subject variants

**Given** the catalog contains a numbered subject family

**When** the user supplies accent/case variants or Arabic/Roman numbering

**Then** the corresponding canonical level is selected, distinct levels remain
distinct, and nonexistent levels are not invented.

## AC-07 — Invalid subject

**Given** no catalog subject matches the supplied expression

**When** the request is processed

**Then** subject-not-found is reported and `Parciales` is not queried.

## AC-08 — Ambiguous subject

**Given** multiple catalog subjects remain valid after normalization

**When** resolution is attempted

**Then** no arbitrary first result is selected, no partial-date query runs, and
the user is asked to clarify.

## AC-09 — Valid subject without partial dates

**Given** the canonical subject exists but has no `Parciales` rows

**When** the lookup runs

**Then** the assistant reports no registered partial dates for that subject and
does not report subject-not-found.

## AC-10 — One partial date

**Given** one direct `Parciales` row exists for the canonical subject

**When** the result is returned

**Then** its recorded date is included.

## AC-11 — Multiple partial dates

**Given** multiple direct rows exist for the canonical subject

**When** the result is returned

**Then** every row/date is included in deterministic date order, without
inventing academic ordinal semantics.

## AC-12 — Canonical subject name

**Given** a subject resolves successfully

**When** the response is built

**Then** it uses the canonical `Materia.nombre`, not the user’s unnormalized
spelling.

## AC-13 — State cleanup and replacement

**Given** a partial-date query completes and a later explicit query names a
different subject

**When** the second request is processed

**Then** stale `materia`/flow state does not determine the second result.

## AC-14 — Backend failure

**Given** catalog or partial-date access fails

**When** the request is processed

**Then** a controlled error is returned and the failure is not represented as
subject-not-found or no partial dates.

## AC-15 — Partial versus final dates

**Given** one request explicitly mentions a parcial and another mentions a final
or mesa

**When** each is interpreted

**Then** the first selects partial-date consultation and the second selects
final-date consultation.

## AC-16 — Partial dates versus registration

**Given** one request asks when a partial occurs and another asks to register or
reserve a place

**When** each is interpreted

**Then** only the first selects partial-date consultation.

## AC-17 — Inherited authentication and matrícula prerequisites

**Given** authentication or matrícula is missing

**When** the capability is invoked

**Then** the inherited prerequisite behavior is preserved and no schedule data
is fabricated.

## AC-18 — Partial-number semantics are out of scope

**Given** the database has no field representing “primer parcial”, “segundo
parcial”, “parcial 1”, or “parcial 2”

**When** the user uses one of those expressions

**Then** 005 does not promise identification or filtering of a specific partial
number; it only covers the direct schedule rows available for the subject.

**Status:** OUT OF SCOPE — unsupported by the current database contract.

## AC-19 — Subject-only language is contextual

**Given** a standalone subject is evaluated outside an active partial-date form

**When** it is interpreted in isolation

**Then** it is not treated as an explicit partial-date request; inside the form,
it is accepted as contextual slot input.
