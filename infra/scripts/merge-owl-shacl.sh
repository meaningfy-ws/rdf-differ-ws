#!/bin/bash

# Check for required arguments
if [ "$#" -lt 2 ]; then
  echo "❌ Missing input files."
  echo "Usage: $0 <ontology.ttl> <shapes.ttl> [output.ttl]"
  echo "Example: $0 ontology.ttl shapes.ttl merged_ontology.ttl"
  exit 1
fi

# Check for Jena's sparql CLI
if ! command -v sparql &> /dev/null; then
  echo "❌ 'sparql' command not found."
  echo "Please install Apache Jena and ensure 'sparql' is in your PATH."
  echo "Download: https://jena.apache.org/download/"
  exit 1
fi

# Input files from command line
OWL_FILE="$1"
SHACL_FILE="$2"

# Input files from command line
OWL_FILE="$1"
SHACL_FILE="$2"

# Optional output file name
if [ -n "$3" ]; then
  FINAL_MERGED="$3"
else
  # Output file based on OWL file name
  OWL_BASENAME=$(basename "$OWL_FILE" .ttl)
  FINAL_MERGED="${OWL_BASENAME}_combined.ttl"
fi

# Script basename for prefixing temp files
SCRIPT_NAME=$(basename "$0" .sh)

# Intermediate files (prefixed)
QUERY_FILE="${SCRIPT_NAME}_filter.sparql"
FILTERED_SHACL="${SCRIPT_NAME}_filtered_shacl.ttl"
CLEANED_SHACL="${SCRIPT_NAME}_cleaned_shacl.ttl"
PREFIXES_FILE="${SCRIPT_NAME}_prefixes.ttl"
BODY_FILE="${SCRIPT_NAME}_body.ttl"

echo "🔍 Preparing the SHACL file for merging..."

# Step 1: Create SPARQL query to remove owl:Ontology triples
cat <<EOF > "$QUERY_FILE"
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

CONSTRUCT {
  ?s ?p ?o
}
WHERE {
  ?s ?p ?o .
  FILTER NOT EXISTS {
    ?s rdf:type owl:Ontology
  }
}
EOF
echo "✅ SPARQL filter created"

# Step 2: Run SPARQL query to clean SHACL file
sparql --data "$SHACL_FILE" --query "$QUERY_FILE" --out turtle > "$FILTERED_SHACL"
echo "✅ Removed owl:Ontology statements"

# Step 3: Extract and merge prefixes from both files
grep '^@prefix' "$OWL_FILE" "$SHACL_FILE" | sed 's/^[^:]*://' | sort | uniq > "$PREFIXES_FILE"
echo "✅ Merged and deduplicated prefixes"

# Step 4: Merge prefixes + OWL body + cleaned SHACL
grep -v '^@prefix' "$FILTERED_SHACL" > "$CLEANED_SHACL"
grep -v '^@prefix' "$OWL_FILE" > "$BODY_FILE"
cat "$PREFIXES_FILE" "$BODY_FILE" "$CLEANED_SHACL" > "$FINAL_MERGED"
echo "✅ Final merged file assembled"

# Step 5: Validating the new file
riot --validate ""$FINAL_MERGED""
echo "✅ Final merged file RDF validated"

# Step 5: Cleanup
rm "$QUERY_FILE" "$FILTERED_SHACL" "$CLEANED_SHACL" "$PREFIXES_FILE" "$BODY_FILE"
echo "🧹 Temporary files cleaned up."

echo "🎉 New merged file saved as: $FINAL_MERGED"
