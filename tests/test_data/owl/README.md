# Minimal ePO test data for OWL-core profile

Given the following versions of a dataset:

- **old:** `ePO_sample-4.0.0.orig.ttl`
- **new:** `ePO_sample-4.0.0.upd.ttl`

The **new** file is a _combined_ OWL and SHACL file that contains also
embedded SHACL data, for testing retrieval of certain constraint information
for added resources, such as the domain, range and cardinality, which would
otherwise not be supported/available in the OWL-core profile.

The following are changes comparing **old** to **new**, where _redundant_
refers to redundant appearances in the existing diff'ing/reporting, and _not
captured_ to the non-appearance thereof, due to one reason or another, that may
or may not be a bug:

1. added class **epo:AwardCriterion**
1. deleted class **epo:AdHocChannel**
1. class **epo:AcquiringCentralPurchasingBody** replaced `skos:prefLabel` w/ `rdfs:label` (interpreted as `rdfs:label` added)
1. class **epo:AwardCriterion** added `skos:prefLabel` (redundant, from added class)
1. class **epo:Document** added `skos:prefLabel` _es_ lang
1. class **epo:AccessTerm** deleted `skos:prefLabel`
1. class **epo:AcquiringCentralPurchasingBody** replaced `skos:prefLabel` w/ `rdfs:label` (interpreted as `skos:prefLabel` deleted)
1. class **epo:AdHocChannel** deleted `skos:prefLabel` (redundant, from deleted class)
1. class **epo:AwardCriteriaSummary** updated `skos:prefLabel` (moved original value to `skos:altLabel`)
1. class **epo:AcquiringCentralPurchasingBody** replaced `skos:prefLabel` w/ `rdfs:label` (interpreted as `skos:prefLabel` changed to `rdfs:label`)
1. class **epo:AwardCriteriaSummary** changed `skos:prefLabel` to `skos:altLabel` (cross-property move of `skos:prefLabel` to `skos:altLabel`)
1. class **epo:AwardCriteriaSummary** add `skos:altLabel` (redundant, from cross-property move of `skos:prefLabel`)
1. class **epo:AwardCriterion** added `skos:definition` (redundant, from added class)
1. class **epo:AdHocChannel** deleted `skos:definition` (redundant, from deleted class)
1. class **epo:AwardCriterion** added `rdfs:subClassOf` (redundant, from added class)
1. class **epo:AdHocChannel** deleted `rdfs:subClassOf` (redundant, from deleted class)
1. class **epo:AwardCriterion** added `rdfs:isDefinedBy` (redundant, from added class)
1. class **epo:AdHocChannel** deleted `rdfs:isDefinedBy` (redundant, from deleted class)
1. class **epo:AdHocChanel** moved `rdfs:isDefinedBy` to **epo:AwardCriterion** (redundant, part of added class)
1. added objectProperty **epo:followsRulesSetBy** with domain `epo:PurchaseContract`, range `epo:FrameworkAgreement` and maxCardinality 1
1. deleted objectProperty **epo:exposesChannel**
1. objectProperty **epo:exposesInvoiceeChannel** added `rdfs:label`
1. objectProperty **epo:followsRulesSetBy** added `skos:prefLabel` (redundant, from added objectProperty)
1. objectProperty **epo:exposesChannel** deleted `skos:prefLabel` (redundant, from deleted objectProperty)
1. objectProperty **epo:describesResultNotice** added `skos:altLabel`
1. objectProperty **epo:followsRulesSetBy** added `rdfs:isDefinedBy` (redundant, from added objectProperty)
1. objectProperty **epo:exposesChannel** deleted `rdfs:isDefinedBy` (redundant, from deleted objectProperty)
1. objectProperty **epo:exposesChannel** moved `rdfs:isDefinedBy` to **epo:followsRuleSetBy** (redundant, part of added class)
1. added datatypeProperty **epo:describesObjectiveParticipationRules**
1. deleted datatypeProperty **epo:describesProfessionRelevantLaw**
1. datatypeProperty **epo:describesProfession** added `rdfs:label` no lang
1. datatypeProperty **epo:describesObjectiveParticipationRules** added `skos:prefLabel` (redundant, from added datatypeProperty)
1. datatypeProperty **epo:describesProfessionRelevantLaw** deleted `skos:prefLabel` (redundant, from deleted datatypeProperty)
1. datatypeProperty **epo:describesObjectiveParticipationRules** added `rdfs:isDefinedBy` (redundant, from added datatypeProperty)
1. datatypeProperty **epo:describesProfessionRelevantLaw** deleted `rdfs:isDefinedBy` (redundant, from deleted datatypeProperty)
1. datatypeProperty **epo:describesProfessionRelevantLaw** moved `rdfs:isDefinedBy` to **epo:describesObjectiveParticipationRules** (redundant, part of added class)
1. datatypeProperty **epo:describesVerificationMethod** converted to objectProperty (not captured)
1. objectProperty **epo:distributesOffer** deleted lang of `skos:prefLabel` (not captured)
1. objectProperty **epo:actsOnBehalfOf** replace lang en w/ de of `skos:prefLabel` (not captured)

There is no automated test case at present using these files, but they can be
used to facilitate manual tests in the meantime.
