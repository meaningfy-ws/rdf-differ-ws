Feature: OWL diffing

  Background:
    Given the OWL files "tests/test_data/owl/ePO_sample-4.0.0.orig.ttl" and "tests/test_data/owl/ePO_sample-4.0.0.upd.ttl"
    And the test prefixes are defined

  Scenario Outline: Diffing example resources in the OWL sample
    When the diff is run
    Then the report should contain the change for "<type>","<instance>","<operation>","<parent>","<new_value>"

    Examples:
      | type            | instance              | operation | parent                             | new_value  |
      | class           | epo:AwardCriterion    | added     |                                    |            |
      | data_property   | skos:prefLabel        | changed   | epo:AcquiringCentralPurchasingBody | rdfs:label |
      | object_property | epo:followsRulesSetBy | added     |                                    |            |
