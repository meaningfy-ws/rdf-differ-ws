# Capability: diff-semantics

Cites EPIC: resolve-open-issues. Issues: #142, #143.

## Requirement: Language-tag changes are captured as updates

When a property value keeps its lexical text but changes or loses its language tag between
versions, the `updated_property` queries SHALL report it as an update.

### Scenario: language tag changed
- **Given** an instance has `prop "text"@en` in the old version and `prop "text"@fr` in the new
- **When** the `updated_property` query runs
- **Then** the change SHALL appear as an `updated` action with old value `"text"@en` and new
  value `"text"@fr`

### Scenario: language tag removed
- **Given** an instance has `prop "text"@en` in the old version and `prop "text"` in the new
- **When** the `updated_property` query runs
- **Then** the change SHALL appear as an `updated` action

## Requirement: Datatype↔object property changes are captured

When a property's value changes between a literal (datatype property) and an IRI (object
property) for the same instance and property, the change SHALL surface (at minimum as an
update), not vanish from the report.

### Scenario: literal becomes IRI
- **Given** an instance has `prop "text"` (literal) in the old version and `prop <iri>` in the new
- **When** the diff queries run
- **Then** the change SHALL appear as an `updated` action with old value `"text"` and new value `<iri>`

### Scenario: unchanged value is not a false positive
- **Given** an instance has `prop "text"@en` in both versions
- **When** the `updated_property` query runs
- **Then** no update SHALL be reported for that value
