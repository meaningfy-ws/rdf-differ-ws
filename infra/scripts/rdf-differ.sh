#!/bin/bash

# Default values
BASE_URL="http://api.localhost" # this will change depending on whether used locally, with or without traefik, or through docker exec
DEFAULT_PROFILE="owl-core-en-only"
DEFAULT_TEMPLATE="json"

# Help message
show_help() {
    echo "Usage: rdf-differ.sh [OPTIONS] COMMAND"
    echo
    echo "Commands:"
    echo "  diff        Create a diff between two RDF files"
    echo "  report      Generate a report for an existing diff"
    echo "  full        Perform both diff and report (default)"
    echo "  list        List diffs (GET /diffs)"
    echo
    echo "Options:"
    echo "  -h, --help                Show this help message"
    echo "  --base-url URL           Base URL for RDF Differ API (default: ${BASE_URL})"
    echo "  --old FILE               Old version TTL file (required for diff)"
    echo "  --new FILE               New version TTL file (required for diff)"
    echo "  --dataset-id ID          Dataset ID (required for report, auto-generated for diff)"
    echo "  --profile PROFILE        Application profile (default: ${DEFAULT_PROFILE})"
    echo "  --template TYPE          Template type (default: ${DEFAULT_TEMPLATE})"
    echo "  --output DIR             Output directory (default: ./diff-output)"
    echo
    echo "Example:"
    echo "  $0 --old first.ttl --new second.ttl full"
    echo "  $0 --dataset-id abc123 report"
}

# Function to wait for a task to complete
wait_for_task() {
    local task_id=$1
    local description=$2
    local print_mode=$3
    [[ "$print_mode" == "print" ]] && echo "⏳ Waiting for ${description} task (${task_id}) to complete..."
    while true; do
        local STATUS=$(curl -s -L -k "${BASE_URL}/tasks/${task_id}" -H 'accept: application/json' | jq -r '.status')
        [[ "$print_mode" == "print" ]] && echo "   Task status: ${STATUS}"
        if [[ "${STATUS}" == "SUCCESS" ]]; then
            [[ "$print_mode" == "print" ]] && echo "✅ Task completed successfully"
            break
        elif [[ "${STATUS}" == "FAILED" || "${STATUS}" == "ERROR" ]]; then
            [[ "$print_mode" == "print" ]] && echo "❌ Task failed!"
            exit 1
        fi
        sleep 5
    done
}

# Function to create a diff
create_diff() {
    local old_file=$1
    local new_file=$2
    local print_mode=$3
    local DATASET_ID=""
    if [[ ! -f "${old_file}" ]]; then
        [[ "$print_mode" == "print" ]] && echo "❌ Old version file not found: ${old_file}"
        exit 1
    fi
    if [[ ! -f "${new_file}" ]]; then
        [[ "$print_mode" == "print" ]] && echo "❌ New version file not found: ${new_file}"
        exit 1
    fi
    [[ "$print_mode" == "print" ]] && echo "🚀 Creating diff..."
    local RESPONSE=$(curl -skLX POST \
        "${BASE_URL}/diffs" \
        -H 'accept: */*' \
        -H 'Content-Type: multipart/form-data' \
        -F 'dataset_description=differ' \
        -F 'dataset_name=diffus' \
        -F 'dataset_id=diff' \
        -F 'dataset_uri=http://diff.com' \
        -F "new_version_file_content=@${new_file};type=text/turtle" \
        -F 'new_version_id=new' \
        -F "old_version_file_content=@${old_file};type=text/turtle" \
        -F 'old_version_id=old')
    [[ "$print_mode" == "print" ]] && echo "📥 Raw response from Create diff:"
    [[ "$print_mode" == "print" ]] && echo "${RESPONSE}"
    if echo "${RESPONSE}" | jq . >/dev/null 2>&1; then
        DATASET_ID=$(echo "${RESPONSE}" | jq -r '.uid')
        [[ "$print_mode" == "print" ]] && echo "✅ Dataset ID: ${DATASET_ID}"
    else
        [[ "$print_mode" == "print" ]] && echo "❌ Create diff failed or returned non-JSON:"
        [[ "$print_mode" == "print" ]] && echo "${RESPONSE}"
        exit 1
    fi
    [[ "$print_mode" == "print" ]] && echo "📡 Getting active tasks..."
    local ACTIVE_TASKS=$(curl -skLX GET "${BASE_URL}/tasks/active" -H 'accept: application/json')
    local TASK_ID=$(echo "${ACTIVE_TASKS}" | jq -r '.[0].id')
    if [ -z "${TASK_ID}" ] || [ "${TASK_ID}" == "null" ]; then
        [[ "$print_mode" == "print" ]] && echo "❌ No active tasks found!"
        exit 1
    fi
    [[ "$print_mode" == "print" ]] && echo "Found active task ID: ${TASK_ID}"
    wait_for_task "${TASK_ID}" "diff" "$print_mode"
    echo "${DATASET_ID}"
}

# Function to generate a report
generate_report() {
    local dataset_id=$1
    local ap=${2:-${DEFAULT_PROFILE}}
    local template=${3:-${DEFAULT_TEMPLATE}}
    local output_dir=${4:-"diff-output"}
    
    mkdir -p "${output_dir}"
    
    echo "🚀 Requesting report..."
    local REPORT_REQ=$(jq -n \
        --arg ap "${ap}" \
        --arg ds "${dataset_id}" \
        --arg rebuild "true" \
        --arg tmpl "${template}" \
        '{application_profile:$ap, dataset_id:$ds, rebuild:$rebuild, template_type:$tmpl}')
    
    local REPORT_RESPONSE=$(curl -skLX POST \
        "${BASE_URL}/diffs/report" \
        -H "accept: */*" \
        -H "Content-Type: application/json" \
        -d "${REPORT_REQ}")
    
    echo "📥 Report request response:"
    echo "${REPORT_RESPONSE}" | jq .
    
    local REPORT_TASK_ID=$(echo "${REPORT_RESPONSE}" | jq -r '.task_id // .id')
    if [ -z "${REPORT_TASK_ID}" ] || [ "${REPORT_TASK_ID}" = "null" ]; then
        echo "❌ No report task id in response"
        exit 1
    fi
    echo "✅ Report task id: ${REPORT_TASK_ID}"
    
    wait_for_task "${REPORT_TASK_ID}" "report" "print"
    
    echo "📥 Downloading report file..."
    local DL_URL="${BASE_URL}/diffs/report?dataset_id=${dataset_id}&application_profile=${ap}&template_type=${template}"
    
    echo "→ GET ${DL_URL}"
    curl -skLX GET \
        "${DL_URL}" \
        -H "accept: text/html" \
        -o "${output_dir}/diff.${template}"
    
    if [[ "${template}" == "json" ]]; then
        jq -S . "${output_dir}/diff.json" > "${output_dir}/diff.json.tmp" && mv "${output_dir}/diff.json.tmp" "${output_dir}/diff.json"
    fi
    
    echo "✅ Report saved to ${output_dir}/diff.${template}"
}

# Function to list /diffs endpoint
list_endpoint() {
    echo "🔬 Listing /diffs at ${BASE_URL}/diffs"
    local RESP=$(curl -skLX GET "${BASE_URL}/diffs" -H 'accept: application/json')
    if echo "${RESP}" | jq . >/dev/null 2>&1; then
        echo "📥 Response (JSON):"
        echo "${RESP}" | jq .
    else
        echo "📥 Raw response:"
        echo "${RESP}"
    fi
}

# Parse command line arguments
COMMAND="full"
OLD_FILE=""
NEW_FILE=""
DATASET_ID=""
PROFILE="${DEFAULT_PROFILE}"
TEMPLATE="${DEFAULT_TEMPLATE}"
OUTPUT_DIR="diff-output"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --old)
            OLD_FILE="$2"
            shift 2
            ;;
        --new)
            NEW_FILE="$2"
            shift 2
            ;;
        --dataset-id)
            DATASET_ID="$2"
            shift 2
            ;;
        --ap|--profile)
            PROFILE="$2"
            shift 2
            ;;
        --template)
            TEMPLATE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        diff|report|full|list)
            COMMAND="$1"
            shift
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Validate required arguments based on command
case ${COMMAND} in
    diff|full)
        if [[ -z "${OLD_FILE}" || -z "${NEW_FILE}" ]]; then
            echo "❌ Both --old and --new files are required for diff or full commands"
            show_help
            exit 1
        fi
        ;;
    report)
        if [[ -z "${DATASET_ID}" ]]; then
            echo "❌ --dataset-id is required for report command"
            show_help
            exit 1
        fi
        ;;
esac

# Execute the command
case ${COMMAND} in
    diff)
        create_diff "${OLD_FILE}" "${NEW_FILE}" print
        ;;
    list)
        list_endpoint
        ;;
    report)
        generate_report "${DATASET_ID}" "${PROFILE}" "${TEMPLATE}" "${OUTPUT_DIR}"
        ;;
    full)
        echo "🔬 Using ${BASE_URL}"
        echo "🔄 Performing full diff and report workflow..."
        DATASET_ID=$(create_diff "${OLD_FILE}" "${NEW_FILE}")
        generate_report "${DATASET_ID}" "${PROFILE}" "${TEMPLATE}" "${OUTPUT_DIR}"
        ;;
esac
