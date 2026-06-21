# diff-semantics

Cites EPIC: resolve-open-issues. Issues: #142, #143.

## ADDED Requirements

### Requirement: Language-tag changes are captured as updates

The `updated_property` queries SHALL report a value as an update when it keeps its lexical
text but changes or loses its language tag between versions.

#### Scenario: Language tag changed

- **GIVEN** an instance has `prop "text"@en` in the old version and `prop "text"@fr` in the new
- **WHEN** the `updated_property` query runs
- **THEN** the change SHALL appear as an `updated` action with old value `"text"@en` and new value `"text"@fr`

#### Scenario: Language tag removed

- **GIVEN** an instance has `prop "text"@en` in the old version and `prop "text"` in the new
- **WHEN** the `updated_property` query runs
- **THEN** the change SHALL appear as an `updated` action

### Requirement: Datatype-to-object property changes are captured

The diff SHALL surface a value that changes between a literal (datatype property) and an IRI
(object property) for the same instance and property — at minimum as an update — rather than
letting it vanish from the report.

#### Scenario: Literal becomes IRI

- **GIVEN** an instance has `prop "text"` (literal) in the old version and `prop <iri>` in the new
- **WHEN** the diff queries run
- **THEN** the change SHALL appear as an `updated` action with old value `"text"` and new value `<iri>`

#### Scenario: Unchanged value is not a false positive

- **GIVEN** an instance has `prop "text"@en` in both versions
- **WHEN** the `updated_property` query runs
- **THEN** no update SHALL be reported for that value
