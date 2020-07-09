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
    And an output folder is provided
    When the user requests the diff inventory
    Then the the inventory queries are executed on the endpoint
    And the non-empty query result-sets are writen into output files
    And the result-set file is named based on the query file with a timestamp suffix