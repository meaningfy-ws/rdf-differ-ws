Feature: Web UI journeys
  As a user of the RDF Differ web UI
  I want to list, create and inspect diffs
  So that I can manage dataset comparisons through the browser.

  Scenario: The home page lists the available diffs
    Given the API returns the diffs "alpha" and "beta"
    When I open the home page
    Then the page shows "alpha"
    And the page shows "beta"

  Scenario: Creating a diff redirects to the tasks page
    Given the API accepts the diff creation
    When I submit a valid create-diff form
    Then I land on the active tasks page

  Scenario: An invalid dataset name is rejected without calling the API
    When I submit a create-diff form with the name "bad name"
    Then the form shows a dataset name error

  Scenario: A create-diff submission without a CSRF token is rejected
    When I submit a create-diff form without a CSRF token
    Then the response status is 403

  Scenario: An API failure is shown as a flash message
    Given the API fails to list the diffs
    When I open the home page
    Then the page shows an error flash
