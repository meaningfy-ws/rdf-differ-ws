# Date:  08/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

Feature: Diffing two dataset versions

  As a user,
  I want to execute the diff of two dataset versions,
  so that I can query the insertions and deletions between them.

  Scenario: Diffing two dataset versions
    Given old and new version RDF files
    And mandatory descriptive metadata
    When the user runs the diff calculator
    Then a correct dataset folder structure is created
    And the diff calculator is executed

  Scenario Outline: Controlling the mandatory descriptive metadata
    Given mandatory descriptive metadata
    But the <property> is missing or incorrect
    When the user runs the incomplete diff calculator
    Then an error message is generated indicating the <property> problem
    Examples:
      | property       |
      | dataset        |
      | old_version_id |
      | new_version_id |
      | scheme_uri     |