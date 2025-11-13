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
1. class **epo:AwardCriterion** added `skos:prefLabel` (redundant, from added class)
1. class **epo:AwardCriterion** added `skos:definition` (redundant, from added class)
1. class **epo:AwardCriterion** added `rdfs:subClassOf` (redundant, from added class)
1. class **epo:AwardCriterion** added `rdfs:isDefinedBy` (redundant, from added class)
1. deleted class **epo:AdHocChannel**
1. class **epo:AdHocChannel** deleted `skos:prefLabel` (redundant, from deleted class)
1. class **epo:AdHocChannel** deleted `skos:definition` (redundant, from deleted class)
1. class **epo:AdHocChannel** deleted `rdfs:subClassOf` (redundant, from deleted class)
1. class **epo:AdHocChannel** deleted `rdfs:isDefinedBy` (redundant, from deleted class)
1. class **epo:AcquiringCentralPurchasingBody** `skos:prefLabel` changed to `rdfs:label`
1. class **epo:AcquiringCentralPurchasingBody** added `rdfs:label` (redundant, from changed property)
1. class **epo:AcquiringCentralPurchasingBody** deleted `skos:prefLabel` (redundant, from changed property)
1. class **epo:Document** added `skos:prefLabel` lang _es_
1. class **epo:AccessTerm** deleted `skos:prefLabel`
1. class **epo:AwardCriteriaSummary** updated `skos:prefLabel` (new value; original value moved to `skos:altLabel`)
1. class **epo:AwardCriteriaSummary** changed `skos:prefLabel` to `skos:altLabel` (cross-property move of original `skos:prefLabel` to `skos:altLabel`; could be ignored as the original property was retained with a new value)
1. class **epo:AwardCriteriaSummary** added `skos:altLabel` (redundant, from changed property; could be considered non-redundant if the cross-property move is ignored)
1. added objectProperty **epo:followsRulesSetBy** with domain `epo:PurchaseContract`, range `epo:FrameworkAgreement` and maxCardinality 1
1. objectProperty **epo:followsRulesSetBy** added `skos:prefLabel` (redundant, from added objectProperty)
1. objectProperty **epo:followsRulesSetBy** added `rdfs:isDefinedBy` (redundant, from added objectProperty)
1. deleted objectProperty **epo:exposesChannel**
1. objectProperty **epo:exposesChannel** deleted `skos:prefLabel` (redundant, from deleted objectProperty)
1. objectProperty **epo:exposesChannel** deleted `rdfs:isDefinedBy` (redundant, from deleted objectProperty)
1. objectProperty **epo:exposesInvoiceeChannel** added `rdfs:label`
1. objectProperty **epo:describesResultNotice** added `skos:altLabel`
1. added datatypeProperty **epo:describesObjectiveParticipationRules**
1. datatypeProperty **epo:describesObjectiveParticipationRules** added `skos:prefLabel` (redundant, from added datatypeProperty)
1. datatypeProperty **epo:describesObjectiveParticipationRules** added `rdfs:isDefinedBy` (redundant, from added datatypeProperty)
1. deleted datatypeProperty **epo:describesProfessionRelevantLaw**
1. datatypeProperty **epo:describesProfessionRelevantLaw** deleted `skos:prefLabel` (redundant, from deleted datatypeProperty)
1. datatypeProperty **epo:describesProfessionRelevantLaw** deleted `rdfs:isDefinedBy` (redundant, from deleted datatypeProperty)
1. datatypeProperty **epo:describesProfession** added `rdfs:label` no lang
1. datatypeProperty **epo:describesVerificationMethod** converted to objectProperty (not captured)
1. objectProperty **epo:distributesOffer** deleted `skos:prefLabel` lang (not captured)
1. objectProperty **epo:actsOnBehalfOf** updated `skos:prefLabel` lang _en_ to _de_ (not captured)

There is no automated test case at present using these files, but they can be
used to facilitate manual tests in the meantime.
