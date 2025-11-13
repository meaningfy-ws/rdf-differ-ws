# Minimal ePO test data for SHACL-core profile

Given the following versions of a dataset:

- **old:** `ePO_shapes_sample-4.0.0.orig.ttl`
- **new:** `ePO_shapes_sample-4.0.0.upd.ttl`

The following are changes comparing **old** to **new**:

1. update the `rdfs:label` value of a node shape **core-shape:adms-Identifier**
2. update the `sh:name` value of a _property_ shape **core-shape:adms-Identifier-adms-schemaAgency**
3. change the `sh:name` and `sh:description` of a node shape to `rdfs:label` and `rdfs:comment` **core-shape:time-Duration**
4. change the `rdfs:label` and `rdfs:comment` of a _property_ shape to `sh:name` **core-shape:cccev-Constraint-cccev-constrains**
5. update the `sh:sparql`/`sh:select` value of a _property_ shape **core-shape:person-Person-cv-registeredAddress**
6. delete a node shape together with all of its _property_ shapes **core-shape:foaf-Person** / **core-shape:foaf-Person-epo-hasCertification**
7. delete a node shape but leave its _property_ shapes intact **core-shape:epo-Business**
8. delete a _property_ shape along with its reference in the relevant node shape **core-shape:person-Person-foaf-givenName**
9. delete a _property_ shape but leaves its reference in the relevant node shape intact **core-shape:person-Person-person-patronymicName**
10. add a new node shape with three _property_ shapes **core-shape:locn-Address**  
11. add a new _property_ shape for an existing node shape **core-shape:time-Duration-time-hasTimeLength**
12. exchange the `rdfs:label` and `rdfs:comment` between two node shapes
13. exchange the `sh:name` and `sh:description` between two _property_ shapes
14. exchange the `sh:targetClass` between two node shapes **core-shape:time-Duration**, **core-shape:epo-Period**
15. exchange the `sh:path` between two _property_ shapes **core-shape:person-Person-epo-hasCountryOfBirth**, **core-shape:person-Person-epo-hasNationality**
16. update the `sh:targetClass` value of a node shape **core-shape:person-Person**
17. update the `sh:path` value of a _property_ shape **core-shape:adms-Identifier-epo-hasScheme**
18. update the `sh:datatype` value of a _property_ shape **core-shape:adms-Identifier-epo-hasScheme**
19. add missing `rdfs:label` and `rdfs:comment` to a node shape **core-shape:cccev-Constraint**
20. add missing `sh:name` and `sh:description` to a _property_ shape **core-shape:cccev-Constraint-epo-hasThresholdType**
21. delete the `rdfs:label` of a _property_ shape where an `sh:name` exists **core-shape:person-Person-dct-alternative**
22. delete the `sh:name` of a node shape where an `rdfs:label` exists **core-shape:cccev-InformationConcept**
23. delete an `rdfs:seeAlso` value of the `owl:Ontology`
24. update the `owl:versionInfo` and `owl:versionIRI` values of the `owl:Ontology`

There is no automated test case at present using these files, but they can be
used to facilitate manual tests in the meantime.
