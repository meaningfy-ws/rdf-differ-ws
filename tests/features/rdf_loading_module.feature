Feature: RDF Loading Module — in-memory diff
  As a user of RDF Differ
  I want to compute a SKOS-history diff entirely in memory
  So that I can diff two vocabulary versions without an external triple store.

  Scenario Outline: Compute insertions and deletions in memory
    Given two RDF vocabulary versions that differ by one added and one removed triple
    When I load and diff them with the <engine> engine
    Then the insertions count is 1
    And the deletions count is 1
    And the store validates

    Examples:
      | engine   |
      | oxigraph |
      | rdflib   |
