@integration
Feature: Remote diff pipeline (end-to-end)
  As an operator running the full stack
  I want creating a diff via the API to enqueue a background task
  So that the asynchronous pipeline is wired correctly.

  # Needs a live stack (make start-services-test). Excluded from the default run by the
  # @integration marker; the downstream skos-history computation is the rdf-loading-module epic.

  Scenario: Creating a diff against the live API returns a task id
    Given a reachable RDF Differ API
    When I post two RDF versions to create a diff
    Then the API responds with a task uid
