Feature: RDF loading and diff edge cases (in-memory)
  As the loading & diffing capability
  I want robust behaviour on boundary and error inputs
  So that diffs are correct and failures are explicit.

  Scenario Outline: Identical versions produce an empty delta
    Given two identical RDF vocabulary versions
    When I load and diff them with the <engine> engine
    Then the insertions count is 0
    And the deletions count is 0

    Examples:
      | engine   |
      | rdflib   |
      | oxigraph |

  Scenario Outline: A real sample OWL pair yields a non-empty delta
    Given the sample OWL versions from the test data
    When I load and diff them with the <engine> engine
    Then the total delta is greater than 0

    Examples:
      | engine   |
      | rdflib   |
      | oxigraph |

  Scenario: A non-existent version file is rejected at configuration time
    When I build a version configuration pointing at a missing file
    Then a configuration error is raised
