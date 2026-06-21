Feature: Report delivery in the web UI
  As a user of the RDF Differ web UI
  I want to build a report, know when it is ready, and view or download it
  So that I can actually obtain the diff report without guessing when it finished.

  Scenario: A built report can be viewed live in the browser
    Given a dataset with a built "html" report for profile "skos-core-en-only"
    When I open the View action for that report
    Then the report is served inline
    And the response content type is for HTML

  Scenario: A built report can be downloaded as a file
    Given a dataset with a built "html" report for profile "skos-core-en-only"
    When I open the Download action for that report
    Then the response is served as an attachment

  Scenario: Building a report shows a progress indicator on the dataset view
    Given the API accepts a report build and returns a task id
    When I submit a report build for profile "skos-core-en-only" and type "html"
    Then I am taken to the dataset view with a building indicator for "skos-core-en-only" · "html"

  Scenario: A completed build is reported as ready
    Given a report build task that has completed successfully
    When the dataset view polls the task status
    Then the status endpoint reports the task as successful

  Scenario: A failed build is reported as failed, not stuck building
    Given a report build task that has failed
    When the dataset view polls the task status
    Then the status endpoint reports the task as failed

  Scenario: Viewing a report that was never built is handled gracefully
    Given no report exists for the requested dataset, profile and type
    When I open the View action for that report
    Then I am redirected with a clear message instead of an error
