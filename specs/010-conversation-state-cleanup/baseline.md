# 010 — Conversation State Cleanup — Baseline

## Pre-refactor state

`flujo_actual` was declared as both an entity and a custom text slot with
`influence_conversation: true`. No NLU example populated it and no Python
action read it. Actions across 001–008 nevertheless wrote or cleared it.

The only runtime consumers were three rules:

- `consultar_asistencia`: reactivated `asistencia_form`;
- `consultar_requerimientos_materia`: reran the requirements action directly;
- `consultar_materias`: reran the course-record action directly.

The latter two rules could not collect the missing input they purported to
recover. Tests mostly asserted emitted slot events rather than end-to-end
conversation recovery.

## Baseline capability matrix

| Capability | Form | Uses materia | Validator | Resolver before submit | Invalid reaches action | Reads flow | Writes flow | Retry worked end-to-end |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 001 Attendance | `asistencia_form` | yes | no | no | yes | rule | yes | partial/legacy |
| 002 Grades | `notas_form` | yes | no | no | yes | no | yes | no |
| 003 Requirements | `requisitos_form` | yes | no | no | yes | rule | yes | no/repeat risk |
| 004 Final dates | `consultar_mesas_form` | yes | no | no | yes | no | yes | no |
| 005 Partial dates | `fechas_parciales_form` | yes | no | no | yes | no | yes | no |
| 006 Registration | `inscripcion_mesa_form` | yes | yes | yes | normally no | no | yes | yes |
| 007 Cancellation | `cancelar_mesa_form` | yes | no | no | yes | no | yes | no |
| 008 Course records | `materias_form` | no | no | n/a | n/a | rule | yes | form path yes |
| 009 FAQs | none | no | n/a | n/a | n/a | no | no | n/a |

## Requirements matrícula audit

Before 010, `ActionConsultarRequerimientosMateria` required authentication,
matrícula, and materia. The form collected only materia. Inspection of the
query showed that matrícula was never used: the action resolves materia and
queries `MateriaEquivalencia` with `materia_codigo`. It affects neither the DB
query, authorization, authentication, nor any business rule. The dependency
was inherited legacy state and conflicted with the form contract.

## Retry baseline

Except for 006, subject resolution occurred in business actions after the form
had submitted and `active_loop` had become null. Clearing `materia` at that
point did not itself restore form ownership. Several actions wrote
`flujo_actual`, but no corresponding rule consumed those values.

The historical Attendance `test_no_matching_subject` mismatch exposed this
design drift: the meaningful behavior is discarding invalid `materia` while a
form keeps requesting it, not clearing or preserving a generic flow marker.

## Baseline reference classes

- Production reads: three conditional rules.
- Production writes: `actions/actions.py`, `actions/actionsMaterias.py`, and
  `actions/actionsMesaExamen.py`.
- Domain state: entity plus influential custom slot.
- Production story state: one interactive Attendance story.
- Current tests: action tests for 001–008 and three mesa story assertions.
- Historical documentation: capability baselines/results that describe the
  architecture at their respective completion time.

Historical documentation is retained; it is not rewritten to imply the legacy
state never existed.

