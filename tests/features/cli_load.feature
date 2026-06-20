Feature: rdf-diff CLI load command
  As an operator
  I want to run loads and diffs from the command line
  So that I can compute diffs without the web service.

  Scenario: Load and diff two versions with the in-memory rdflib engine
    Given a load configuration for the sample OWL versions
    When I run "load" with the rdflib engine and an output directory
    Then the command exits successfully
    And a "result.json" artifact is written

  Scenario: Missing the required config option fails
    When I run "load" with no config option
    Then the command exits with an error

  Scenario: A configuration with a missing version file fails
    Given a load configuration pointing at a missing version file
    When I run "load" with the rdflib engine and an output directory
    Then the command exits with an error
