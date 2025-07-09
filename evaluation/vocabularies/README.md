# Vocabularies

This folder contains some pairs of RDF/OWL vocabularies to compare an old and new version using RDF Differ and other similar RDF diff tools like the OWL Difference Protégé plugin.

- **ePO_core** TTL format of the eProcurement Ontology (ePO) versions [4.1.0](https://github.com/OP-TED/ePO/blob/v4.1.0/implementation/ePO_core/owl_ontology/ePO_core.ttl) and [4.2.0](https://github.com/OP-TED/ePO/blob/v4.2.0/implementation/ePO_core/owl_ontology/ePO_core.ttl), and their corresponding `-no-imports` modified copies with imports removed (to work with tools like OWL Difference that raise an error for unresolvable imports).

- **form-type-skos** SKOS RDF format of [an EU Vocabulary](https://op.europa.eu/en/web/eu-vocabularies/dataset/-/resource?uri=http://publications.europa.eu/resource/dataset/form-type) "name authority list" (NAL) aka authority table (AT) used at [TED](https://ted.europa.eu/en/), versions 20240612-0 (2024) and 20250319-0 (2025) known to contain additions of terms.

- **test** TTL format of a simple test vocabulary, two versions "1" and "2" for comparing simple changes.
