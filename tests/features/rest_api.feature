Feature: REST API journeys
  As a client of the RDF Differ REST API
  I want predictable status codes and a problem-style error body
  So that I can drive diffs and reports programmatically.

  Scenario: Listing diffs returns the known datasets
    Given the triplestore holds datasets "alpha" and "beta"
    When I GET "/diffs"
    Then the status is 200
    And the JSON array has 2 entries

  Scenario: An unknown dataset yields a problem-style 404
    Given the triplestore has no matching dataset
    When I GET "/diffs/missing"
    Then the status is 404
    And the problem body has title "Not Found"

  Scenario: Creating a diff enqueues a task
    Given the triplestore accepts a new dataset and the queue is available
    When I POST a valid multipart diff to "/diffs"
    Then the status is 200
    And the response has a "uid"

  Scenario: The OpenAPI document is served
    When I GET "/openapi.json"
    Then the status is 200
    And the OpenAPI paths include "/diffs"
