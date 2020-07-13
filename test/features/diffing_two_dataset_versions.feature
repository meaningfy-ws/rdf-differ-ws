# Date:  08/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

Feature: Diffing two dataset versions

  As a user,
  I want to execute the diff of two dataset versions,
  so that I can query the insertions and deletetions between them.

  Scenario: Diffing two dataset versions
    Given alpha and beta RDF files
    And mandatory descriptive metadata
    When the user runs the diff calculator
    Then a correct dataset folder structure is created
    And the files are copied and renamed accordingly in the folder structure
    And a correct configuration file is created
    And the diff calculator is executed

  Scenario Outline: Controlling the mandatory descriptive metadata
    Given mandatory descriptive metadata
    But the <property> is missing or incorrect
    When the user runs the diff calculator
    Then an error message is generated indicating the <property> problem
    Examples:
      | property              |
      | dataset name          |
      | alpha dataset version |
      | beta dataset version  |
      | scheme URI            |