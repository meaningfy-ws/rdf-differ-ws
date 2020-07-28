# Date:  08/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

Feature: List the diffs in the triplestore

  As a user,
  I want to list all the diffs in the triplestore,
  so that I know what is available.

  Scenario: Query the triplestore
    Given the configured endpoint
    And a set of well defined SPARQL queries for inventory checking
    When the user requests the diff inventory
    Then the datasetURI is returned
    And at least two dataset versions are returned
    And the count of deleted and inserted triples are returned