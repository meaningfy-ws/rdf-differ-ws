# Date:  08/07/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com

Feature: Prepare the skos-history config file and folder structure

  As a user,
  I want to structure the dataset folder and generate the skos-history configuration file from a minimal set of parameters,
  so that I can execute the skos-history.

  Scenario: Set up the folder structure
    Given mandatory descriptive metadata
    And the root path of folder structure
    And alpha and beta RDF files
    When the user runs the folder structure generator
    Then a correct dataset folder structure is created
    And a sub-folder is created for each dataset version
    And a dataset file is copied into the version sub-folder
    And the file is renamed to a standard file name

  Scenario: Generating the skos-history config file
    Given mandatory descriptive metadata
    And the root path of folder structure
    When the user runs the config generator
    Then a correct configuration file is created in the folder structure