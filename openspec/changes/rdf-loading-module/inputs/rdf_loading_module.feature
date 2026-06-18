# Feature file for the RDF Loading Module (rewrite of resources/load_versions.sh)
# Source spec: docs/spec/rewriting-sh-to-python/EPIC-rdf-loading-module.md
# Business language only — no SQL, endpoints, or class names.

Feature: RDF Loading Module — load versions and compute delta graphs

  As a vocabulary maintainer,
  I want to load complete vocabulary versions and compute the insertions and deletions
  between them as named graphs,
  so that downstream change reports can be produced — either against a persistent triple
  store or entirely in memory without any server.

  # Each scenario is self-contained: it declares the dataset, versions, and mode it needs.

  # ---------------------------------------------------------------------------
  # Configuration validation (EPIC T1, error matrix, ADR-5)
  # ---------------------------------------------------------------------------

  Scenario Outline: Reject invalid loading configurations before any data is written
    Given a loading configuration that is "<flaw>"
    When the user requests a load
    Then the load is rejected before any graph is written
    And the user is told the reason "<reason>"

    Examples:
      | flaw                          | reason                                  |
      | missing one of two versions   | at least two versions are required      |
      | having duplicate version ids  | version identifiers must be unique      |
      | pointing to a missing file    | version file does not exist             |
      | using a relative scheme URI   | scheme URI must be an absolute IRI      |
      | mixing two RDF file formats   | all version files must share one format |
      | selecting the skolemise policy| skolemise policy is not yet supported   |

  # ---------------------------------------------------------------------------
  # Version loading and version-history metadata (F3–F8, F15)
  # ---------------------------------------------------------------------------

  Scenario: Load two versions and record the version history
    Given a valid configuration with versions "8.14" and "9.0"
    When the user runs the load
    Then a named graph holds the complete content of version "8.14"
    And a named graph holds the complete content of version "9.0"
    And a version history record exists for each version
    And the newer version record points to the older as its previous version
    And the version history identifies "9.0" as the current version

  Scenario Outline: Keep distinct version graphs for awkward version identifiers
    Given a valid configuration with versions "<id_a>" and "<id_b>"
    When the user runs the load
    Then a distinct named graph holds the content of version "<id_a>"
    And a distinct named graph holds the content of version "<id_b>"

    Examples:
      | id_a | id_b |
      | 8.14 | 9.0  |
      | v 1  | v/2  |

  Scenario Outline: Resolve each version's identifier and date from data or configuration
    Given a version whose file "<carries>" an embedded version date
    And the configuration "<supplies>" a date for that version
    When the user runs the load
    Then the version history record records "<recorded>"

    Examples:
      | carries        | supplies | recorded            |
      | carries        | omits    | the embedded date   |
      | does not carry | supplies | the configured date |
      | does not carry | omits    | no date             |

  # ---------------------------------------------------------------------------
  # Delta computation (F9, F12, EPIC T3)
  # ---------------------------------------------------------------------------

  Scenario: Compute insertions and deletions between two versions
    Given version "8.14" and version "9.0" are loaded
    When the deltas are computed for the pair "8.14" to "9.0"
    Then the insertions graph contains exactly the triples present in "9.0" but absent from "8.14"
    And the deletions graph contains exactly the triples present in "8.14" but absent from "9.0"
    And the delta is described as having one insertions part and one deletions part
    And the delta records that it goes from "8.14" to "9.0"

  Scenario: Identical versions produce empty deltas
    Given version "8.14" and version "9.0" have identical content
    When the deltas are computed for the pair "8.14" to "9.0"
    Then the insertions graph is empty
    And the deletions graph is empty

  # ---------------------------------------------------------------------------
  # Delta pair coverage (F13, EPIC T4)
  # ---------------------------------------------------------------------------

  Scenario Outline: Compute the correct set of delta pairs
    Given a configuration with versions "<versions>"
    And direct-to-current deltas are "<direct>"
    When the user runs the load
    Then deltas are computed for the pairs "<pairs>"

    Examples:
      | versions               | direct   | pairs                                                  |
      | 8.14, 9.0              | enabled  | 8.14->9.0                                              |
      | 8.12, 8.13, 8.14, 9.0  | enabled  | 8.12->8.13, 8.13->8.14, 8.14->9.0, 8.12->9.0, 8.13->9.0|
      | 8.12, 8.13, 8.14, 9.0  | disabled | 8.12->8.13, 8.13->8.14, 8.14->9.0                      |

  # ---------------------------------------------------------------------------
  # Blank-node policy (F10, ADR-5, EPIC T3)
  # ---------------------------------------------------------------------------

  Scenario Outline: Apply the configured blank-node policy during delta computation
    Given a new version that adds one statement with a blank-node subject
    And the blank-node policy is "<policy>"
    When the deltas are computed
    Then the blank-node statement is "<treatment>" in the insertions graph

    Examples:
      | policy        | treatment |
      | exclude       | absent    |
      | document-only | present   |

  # ---------------------------------------------------------------------------
  # Dual-mode parity (L2, ADR-1/2/3, EPIC T6) — the core new capability
  # ---------------------------------------------------------------------------

  Scenario: Produce the same result in memory and against a triple store
    Given a valid configuration with versions "8.14" and "9.0"
    When the user runs the load in in-memory mode
    And the user runs the same load in remote mode
    Then the insertion and deletion counts match between the two modes
    And the same set of named graphs is produced in both modes

  Scenario: Run a temporary diff in memory without any triple store
    Given a valid configuration with versions "8.14" and "9.0"
    And the loading mode is "in-memory"
    And no triple store is available
    When the user runs the load
    Then the load completes successfully
    And the insertions and deletions graphs can be exported as RDF files

  # ---------------------------------------------------------------------------
  # Idempotency (L5, EPIC T5)
  # ---------------------------------------------------------------------------

  Scenario: Re-running the load produces equivalent graph state
    Given a configuration that has already been loaded once
    When the user runs the same load again
    Then each delta graph is cleared before it is recomputed
    And the resulting insertion and deletion counts are unchanged
    And no stale triples remain from the previous run

  # ---------------------------------------------------------------------------
  # Validation (L8, EPIC T7)
  # ---------------------------------------------------------------------------

  Scenario: Fail when a version file cannot be parsed as RDF
    Given a configuration whose version "9.0" file is not valid RDF
    When the user runs the load
    Then the load stops and reports a graph-load error naming version "9.0"

  Scenario: Fail when a loaded version graph is unexpectedly empty
    Given a configuration whose version "9.0" file contains no statements
    When the user runs the load
    Then the load reports a validation failure naming the empty version

  Scenario: Fail when an insertions graph contains a triple already present in the old version
    Given a completed load whose insertions graph contains a triple that is also in the old version
    When the store is validated
    Then the validation fails and identifies the offending insertions graph

  # ---------------------------------------------------------------------------
  # Error handling for the remote backend (error matrix, EPIC T8)
  # ---------------------------------------------------------------------------

  Scenario Outline: Surface triple-store transport failures clearly
    Given the loading mode is "remote"
    And the triple store responds with "<failure>" during "<step>"
    When the user runs the load
    Then the load stops and reports a graph-store error
    And the error message includes the reported "<failure>"

    Examples:
      | step            | failure             |
      | uploading data  | a server error      |
      | computing delta | an update rejection |
      | validation      | a query timeout     |

  Scenario: Retry a transient remote failure before aborting
    Given the loading mode is "remote"
    And the triple store fails transiently while uploading data
    When the user runs the load
    Then the failing remote step is retried according to the configured retry policy
    And the load aborts with a graph-store error only after the retries are exhausted
