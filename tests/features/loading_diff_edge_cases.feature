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

  Scenario: Both engines compute the same delta for the same input
    Given the sample OWL versions from the test data
    When I load and diff them with both engines
    Then both engines report the same insertions and deletions

  Scenario: A three-version history where the third restores the first is consistent
    Given three OWL versions where the third restores the first
    When I load and diff the three versions with the rdflib engine
    Then the v1->v2 and v2->v3 deltas are mirror images
    And the v1->v3 delta is empty

  Scenario: Excluding blank nodes yields a smaller delta than documenting them
    Given the sample SHACL versions from the test data
    When I diff them with the exclude and document_only policies
    Then the exclude policy reports fewer changes than document_only

  Scenario: An empty version graph fails validation
    Given a version configuration whose second version file is empty
    When I load and validate it with the rdflib engine
    Then a validation error is raised

  Scenario: Mixed version file formats are rejected at configuration time
    When I build a version configuration mixing turtle and rdf-xml files
    Then a configuration error is raised
