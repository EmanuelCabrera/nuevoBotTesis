# 009 — Institutional FAQs / Información institucional — Specification

## Purpose

Capability 009 is the current static FAQ catalog for general UGD information.
It answers explicit institutional questions through response templates declared
in `domain.yml`.

This specification inventories existing behavior only. It does not validate
the institutional facts against the internet, invent new facts, or turn broad
requests such as “necesito información” into an arbitrary FAQ.

## Architecture

The intended FAQ path is:

```text
explicit institutional intent
→ direct Rasa rule
→ static domain utterance
```

There are no FAQ custom actions, Supabase queries, forms, required slots,
entities, active loops, authentication requirements, or `flujo_actual` state.
Each supported FAQ intent has one direct rule in `data/rules.yml`. The
redundant FAQ-only stories were removed; unrelated greeting, farewell, and
authentication stories remain.

## Current FAQ catalog

All response content is static and hard-coded in `domain.yml`.

| Intent | Examples | Supported question | Response route | Current answer summary | Source class |
|---|---:|---|---|---|---|
| `requisitos_inscripcion` | 29 | Documents and administrative admission requirements | `utter_respuesta_requisito_inscripcion` | DNI, birth certificate, secondary title, health/group certificate, photos, folder, and anticipatory-course proof | B |
| `plazos_inscripcion` | 26 | Months and deadlines for career admission | `utter_respuesta_plazos_inscripcion` | General September–March period and an exceptional June intake for Contador Nacional Público | B |
| `evaluacion_coneau` | 28 | Institutional authorization/accreditation history | `utter_respuesta_evaluacion_coneau` | CONEAU and ministry evaluation history, 1998 authorization, 2007 external evaluation, and 2009 definitive authorization | B |
| `curso_ingreso` | 31 | Existence and format of the leveling course | `utter_respuesta_curso_ingreso` | September–December Saturday course, February/March course, and a July option for some careers | B |
| `informar_modalidad_inscripcion` | 28 | Whether career enrollment is in person or remote | `utter_respuesta_informar_modalidad_inscripcion` | Enrollment is personal; the answer also states a parent must attend for students under 21 | B |
| `visitas_consultas` | 27 | Visiting UGD and its facilities | `utter_respuesta_visitas_consultas` | States only that UGD's doors are open to visitors | B |
| `informar_becas_hermanos` | 26 | Scholarships and sibling discounts | `utter_respuesta_informar_becas_hermanos` | General scholarship system and a 15% discount for one sibling | B |
| `informar_horarios_trabajadores` | 26 | Schedule options for working students | `utter_respuesta_informar_horarios_trabajadores` | Claims schedules support work, mentions internships and semi-presential third/fourth-year subjects | B |
| `informar_intercambio_de_estudio` | 14 | Academic exchanges and partner universities | `utter_respuesta_intercambio_de_estudio` | Agreements with Vigo and Guadalajara and planned agreements with UNIJUI/FEMA | B |
| `informar_equivalencias` | 15 | Recognition of studies completed elsewhere | `utter_respuesta_equivalencias` | Case-by-case evaluation using plans, certification, workload, bibliography, content, and agreements | B |
| `informar_examen_recuperatorio` | 15 | General exam, recovery, regularity, and grading policy | `utter_respuesta_examen_recuperatorio` | Partial, recovery, and final exam overview; modalities and minimum passing grade of 4 | B |
| `informar_asistencia` | 67 | General attendance policy | `utter_respuesta_asistencia` | 80% attendance, card registration, and a stated possible 50% special regime | B |
| `informar_ayuda_informatica_ingles` | 12 | Academic support for computing and English | `utter_respuesta_informar_ayuda_informatica_ingles` | Subjects in curricula, consultation classes, and possible direct final examination authorization | B |
| `informar_nivel_profesores` | 13 | Qualifications and academic level of teachers | `utter_respuesta_informar_nivel_profesores` | Ministry requirements and a claim that more than 70% have postgraduate studies | B |
| `informar_equipamiento_tecnologico` | 13 | Laboratories and technological infrastructure | `utter_respuesta_informar_equipamiento_tecnologico` | Four computer laboratories, a Cisco telecommunications laboratory, and institutional systems | B |
| `informar_servicios` | 13 | General student services and benefits | `utter_respuesta_informar_servicios` | Personalized attention, library, laboratories, sports, student affairs, and benefits | B |
| `contactos` | 10 | Telephone/email/contact information | `utter_contactos` | Links to the UGD contact page rather than embedding contact values | A |

Source classifications:

- **A**: the answer points to an explicit source rather than asserting mutable
  values directly;
- **B**: institutional facts are hard-coded, but no independent supporting
  repository/data source or freshness metadata was found;
- **C**: dynamic database content;
- **D**: unclear.

No FAQ is class C or D. README lists many of the FAQ categories as product
scope, but it does not substantiate the detailed facts in the responses.

## Source-of-truth limitations

The repository contains no thesis requirement, institutional data file, CMS,
FAQ table, or source timestamp for these answers. Git history contains the
same YAML implementation but no supporting institutional document. Except for
the contact-page link, `domain.yml` is both delivery mechanism and sole factual
source.

Facts with especially high staleness risk include dates, age requirements,
scholarship percentage, partner institutions, laboratory counts, course
formats, attendance percentages, and staff qualification percentages.

## Semantic boundaries

- `informar_asistencia` is institutional policy; `consultar_asistencia` is a
  student's personal attendance for a subject.
- `requisitos_inscripcion`, `plazos_inscripcion`, and
  `informar_modalidad_inscripcion` concern admission to the university;
  `inscribirse_mesa_examen` and `cancelar_inscripcion_mesa_examen` are
  transactional final-exam operations.
- `informar_equivalencias` concerns recognition of prior studies;
  `consultar_requerimientos_materia` returns prerequisites for a specific
  subject.
- `informar_examen_recuperatorio` describes general exam policy;
  final/partial date intents retrieve dates for a subject.
- `informar_servicios` describes institutional services;
  `informar_equipamiento_tecnologico` is limited to technology and facilities.
- `visitas_consultas` concerns visits/access to staff; `contactos` returns the
  contact-directory link.
- `consultar_materias`, `consultar_notas`, and other personal capabilities are
  not FAQ routes.

## Generic language

The following phrases do not deterministically identify any FAQ and are not
part of the positive FAQ contract:

- “necesito información”;
- “qué puedo hacer”;
- “ayuda”;
- “cómo funciona”;
- “qué necesito”;
- “qué opciones tengo”.

They may be evaluated as ambiguous/out-of-scope baseline cases, but 009 must
not force them into a specific institutional answer.

## Dialogue and state contract

An explicit FAQ should be answerable directly without authentication or slot
collection. After a response, no loop or FAQ state remains active. A second
explicit FAQ should route independently.

The baseline identified one production wiring defect:
`informar_nivel_profesores` was declared in the domain and NLU and had a static
response, but no story or rule routed it to that response. The cleanup adds its
direct rule and direct Core coverage.

## Explicit non-goals

- No internet fact verification in this phase.
- No new institutional categories or facts.
- No FAQ intent consolidation or removal.
- No conversion to Supabase/CMS.
- No dynamic institutional data source or unsupported institutional facts.
- No changes to capabilities 001–008.
