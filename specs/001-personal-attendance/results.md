# Personal Attendance — Final Results

## Test environment

Rasa was executed with the repository's existing Docker environment. The
available image was `nuevobottesis-rasa-server:latest`, reporting:

- Rasa 3.6.20
- Rasa SDK 3.6.2
- Python 3.10.19

The repository documents the `rasa-bot` service in `docker-compose.yml` and
uses `docker-compose up --build` for normal startup. For isolated verification,
the existing Rasa image was run directly with the workspace mounted. A
temporary Docker-managed volume stored the freshly trained model without
writing model artifacts into the repository.

Relevant commands executed:

```bash
docker run --rm nuevobottesis-rasa-server:latest rasa --version
docker volume create personal_attendance_models
docker run --rm --user 0 \
  -v "$PWD:/app" \
  -v personal_attendance_models:/out \
  -w /app \
  nuevobottesis-rasa-server:latest \
  sh -lc 'rm -f /out/* && rasa train --out /out'
```

Fresh NLU verification:

```bash
docker run --rm \
  -v "$PWD:/app" \
  -v personal_attendance_models:/out \
  -w /app \
  nuevobottesis-rasa-server:latest \
  sh -lc 'MODEL=$(ls /out/*.tar.gz | head -1); \
  rasa test nlu --nlu tests/nlu_attendance_test.yml \
  --model "$MODEL" --out /tmp/nlu_results'
```

For the STEP 8B stability check, three additional NLU-only models were
trained from the same `data/nlu.yml` and evaluated independently:

```bash
docker run --rm --user 0 -v "$PWD:/app" -v personal_attendance_models:/out -w /app \
  nuevobottesis-rasa-server:latest sh -lc \
  'for i in 1 2 3; do rasa train nlu -u data/nlu.yml \
   --fixed-model-name run$i --out /out/final_stability2/run$i; done'
```

Fresh dialogue and Core controls used the same image and model:

```bash
docker run --rm -v "$PWD:/app" -v personal_attendance_models:/out -w /app \
  nuevobottesis-rasa-server:latest \
  sh -lc 'MODEL=$(ls /out/*.tar.gz | head -1); \
  rasa test core --stories tests/test_attendance_stories.yml \
  --model "$MODEL" --out /tmp/core_attendance'

docker run --rm -v "$PWD:/app" -v personal_attendance_models:/out -w /app \
  nuevobottesis-rasa-server:latest \
  sh -lc 'MODEL=$(ls /out/*.tar.gz | head -1); \
  rasa test core --stories tests/test_stories.yml \
  --model "$MODEL" --out /tmp/core_all'
```

The action and resolver suite was run locally with:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Final verification

### NLU

Fresh held-out evaluation:

- Overall: 28/28 (100%)
- Personal attendance: 19/19 (100% precision, recall, and F1)
- General attendance policy: 9/9 (100% precision, recall, and F1)
- `materia`: precision 100%, recall 100%, F1 100% (21 evaluated entities)

The previously unstable boundary case now predicts policy correctly:

```text
¿Cuántas faltas puedo tener?
expected: informar_asistencia
predicted: informar_asistencia
confidence: 73.7%
```

### NLU stability check

All three fresh NLU-only retrainings passed 28/28 (19/19 personal and 9/9
policy). The boundary phrase `¿Cuántas faltas puedo tener?` was classified as
`informar_asistencia` in all three runs, each with 73.7% confidence.

## STEP 8B training change

Only `data/nlu.yml` was changed. No examples were removed. The following
contrastive examples were added to `informar_asistencia`:

- cuál es el tope de inasistencias que admite la cursada
- qué máximo de ausencias permite el reglamento
- hasta qué cantidad de faltas se mantiene la regularidad
- qué máximo de clases puedo perder sin quedar libre
- qué límite de faltas permite la institución
- cuál es la cantidad de faltas que se permite acumular
- cuántas faltas puedo acumular sin perder la regularidad
- cuántas faltas me permite la institución durante la cursada
- cuántas ausencias puedo tener antes de quedar libre
- cuál es el máximo de faltas que puedo registrar según el reglamento
- cuántas faltas puedo tener antes de quedar libre
- cuántas faltas puedo tener y seguir siendo regular
- cuántas faltas puedo tener según el reglamento
- cuál es la asistencia mínima requerida por la institución
- mínimo de asistencia exigido para conservar la regularidad
- porcentaje mínimo obligatorio de asistencia para aprobar
- qué nivel mínimo de asistencia establece el reglamento
- cuántas faltas se pueden tener según la normativa
- cuántas faltas podría tener un alumno sin perder la regularidad
- cuántas faltas están permitidas durante el cursado
- qué cantidad de faltas está permitida por la institución
- cuál es el máximo permitido de ausencias
- cuántas ausencias permite el reglamento académico
- qué límite de inasistencias puedo tener según la universidad
- qué cantidad de faltas admite la universidad

The following current/past-state contrasts were added to
`consultar_asistencia`:

- cuántas faltas llevo acumuladas en este período
- cuántas ausencias figuran en mi registro
- qué cantidad de clases perdí hasta hoy
- cómo está mi porcentaje personal actual
- quiero saber cuántas inasistencias tengo registradas
- cuántas clases dejé de asistir durante la cursada
- cuántas faltas tengo acumuladas ahora
- cuántas ausencias figuran en mi historial
- cuántas inasistencias llevo este cuatrimestre
- cuántas clases falté hasta el momento
- cómo está mi asistencia actual
- cuál es mi porcentaje personal de asistencia

The policy examples emphasize institutional limits, permissions, requirements,
and regularity; the personal examples emphasize the student's own recorded or
accumulated state. This reinforces meaning rather than a single keyword.

### Dialogue

Attendance regression suite:

- 4/4 conversations correct
- Conversation accuracy: 100%
- Action accuracy: 19/19 (100%)

### Action / subject resolution

Unit-test suite:

- 16/16 tests passed

Coverage includes attendance calculations, missing data, backend errors,
canonical catalog identity, accent and case normalization, numbered subjects,
unknown levels, distinct levels, ambiguity, and clarification continuation.

Verified subject contract:

| Expression | Result |
|---|---|
| `fisica` | `Física I` |
| `fisica 1` | `Física I` |
| `fisica i` | `Física I` |
| `fisica 2` | `Física II` |
| `fisica ii` | `Física II` |
| `fisica 3` | `Física III` |
| `fisica iii` | `Física III` |
| `fisica 4` | Not found; no invented subject |
| `algebra` | `Álgebra I` |
| `algebra 2` | `Álgebra II` |

The resolver preserves the catalog record's authoritative identifier and
display name. Different levels are matched by normalized family plus level;
they are never merged. An unnumbered numbered-family expression defaults to
level I. Remaining ambiguity produces clarification and does not execute the
attendance query.

## Baseline comparison

| Area | Baseline | Final |
|---|---:|---:|
| NLU accuracy | 35.7% (10/28) | 100% (28/28) |
| Personal attendance | 10/19 | 19/19 |
| General policy | 0/9 | 9/9 |
| `materia` F1 | 72.2% | 100% |
| Attendance dialogue | 2/4 | 4/4 |
| Action tests | 6/6 | 16/16 |
| Canonical resolution | Not covered | Covered; passing |
| Numbered subject resolution | Not covered | Covered; passing |
| Ambiguity handling | Not covered | Covered; passing |

## Acceptance criteria

| Criterion | Status | Evidence or reason |
|---|---|---|
| AC-01 | PASS | Attendance dialogue scenario A passed; subject-present request completed without requesting the subject again. |
| AC-02 | PASS | All 19 held-out personal-attendance cases passed, including absence-oriented language. |
| AC-03 | PASS | Attendance-oriented personal cases are covered by the 19/19 personal result. |
| AC-04 | PASS | All nine held-out policy cases were classified as `informar_asistencia`; the policy flow does not request `materia`. |
| AC-05 | PASS | The personal-state versus institutional-limit contrast is correct, including `faltas tengo` versus `faltas puedo tener`, across all held-out cases and three retrainings. |
| AC-06 | PASS | Missing-subject attendance scenario passed. |
| AC-07 | PASS | Subject follow-up scenario passed and continued the original flow. |
| AC-08 | PASS | Action tests verify attended, absent, total, percentage, consistency, and requested subject. |
| AC-09 | PASS | Repeated-query scenario passed with subject replacement. |
| AC-10 | PASS | Held-out entity evaluation achieved 100% F1 and representative variation tests passed. |
| AC-11 | PASS | Canonical catalog identity, accent/case normalization, and numbering resolution passed in the unit suite. |
| AC-12 | PASS | Ambiguous matches request clarification and preserve the attendance flow. |
| AC-13 | PASS | Level-I defaulting, Arabic/Roman equivalence, distinct levels, and unknown-level behavior passed. |

## Remaining limitations

- Authentication remains out of scope.
- Matrícula resolution remains out of scope.
- Academic-period behavior remains unchanged.
- Live Supabase behavior is not covered by the mocked action tests.
- Subject-resolution tests use representative catalog records; the complete
  live catalog and its operational data quality were not independently audited.

## Regression control

Attendance-specific results improved from 2/4 to 4/4 conversations and the
attendance action-level result is 19/19.

The pre-existing Core suite produced:

- 5/8 conversations
- 62.5% conversation accuracy
- 27/34 actions correct
- 79.4% action accuracy

The control remains an unrelated legacy suite. Its action-level accuracy
matches the historical 79.4% baseline; conversation accuracy is higher than
the historical 4/8 result. No unrelated regression was identified.

## Closure decision

`001-personal-attendance` can be considered complete for the in-scope
capability. AC-01 through AC-13 are PASS, and the required NLU, dialogue, and
action/resolver suites were freshly executed. Authentication, matrícula,
academic-period behavior, and live Supabase integration remain explicitly out
of scope.

## Implementation/refactor note

Subject resolution now reads the complete canonical subject catalog from
Supabase at runtime. The catalog is cached in memory for 10 minutes, while the
pure resolver is independent from Supabase access and can be reused by future
capabilities. No acceptance behavior changed.
