# Date:  07/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

Feature: Running the skos-history diff of two dataset versions

  As a user,
  I want to run the skos-history script,
  so that a diff of two dataset versions is generated.

  Scenario: Running the skos-history
    Given a correct dataset folder structure
    And a correct configuration file
    When the user runs the skos-history calculator
    Then the dataset versions are loaded into the triplestore
    And the DSV description is generated
    And the insertions and deletions graphs are created
