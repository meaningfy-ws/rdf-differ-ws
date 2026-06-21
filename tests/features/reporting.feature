Feature: Application profile discovery for reporting
  As the reporting component
  I need to discover application profiles, their template variants and queries
  So that diff reports can be built from the correct templates and queries.

  Background:
    Given the application profiles root is the sample AP config

  Scenario: List the available application profiles
    When I list the application profiles
    Then the profiles include "ap1" and "ap2"

  Scenario: List the template variants of a profile
    When I list the template variants of "ap1"
    Then the variants include "html" and "json"

  Scenario: Build the queries dictionary of a profile
    When I build the queries dict of "ap1"
    Then the queries dict is not empty

  Scenario: An unknown application profile is rejected
    When I request the queries folder of "does-not-exist"
    Then a lookup error is raised

  Scenario: A profile without a queries folder is reported
    When I request the queries folder of "ap2"
    Then a file-not-found error is raised
