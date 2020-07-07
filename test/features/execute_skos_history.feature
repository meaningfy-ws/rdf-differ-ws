# Date:  07/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

Feature: Generate the diff of two dataset versions

  As a user,
  I want to execute the diff of two dataset versions,
  so that I can query the insertions and deletetions between them.

  Scenario: Main success scenario
    Given a correct dataset folder structure
    And a correct configuration file
    When the user runs the diff calculator
    Then the dataset versions are loaded into the triplestore
    And the DSV description is generated
    And the insertions and deletions graphs are created

  Scenario: Incorrect config scenario
    Given a correct dataset folder structure
    And an incorrect configuration file
    When the user runs the diff calculator
    Then an error message is generated indicating the config problem

  Scenario: Incorrect folder structure scenario
    Given an incorrect dataset folder structure
    And a correct configuration file
    When the user runs the diff calculator
    Then an error message is generated indicating the folder structure problem
