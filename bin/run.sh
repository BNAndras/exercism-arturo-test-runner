#!/usr/bin/env sh

# Synopsis:
# Run the test runner on a solution.

# Arguments:
# $1: exercise slug
# $2: path to solution folder
# $3: path to output directory

# Output:
# Writes the test results to a results.json file in the passed-in output directory.
# The test results are formatted according to the specifications at https://github.com/exercism/docs/blob/main/building/tooling/test-runners/interface.md

# Example:
# ./bin/run.sh two-fer path/to/solution/folder/ path/to/output/directory/

# If any required arguments is missing, print the usage and exit
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "usage: ./bin/run.sh exercise-slug path/to/solution/folder/ path/to/output/directory/"
    exit 1
fi

slug="$1"
solution_dir=$(realpath "${2%/}")
output_dir=$(realpath "${3%/}")
results_file="${output_dir}/results.json"

mkdir -p "${output_dir}"

echo "${slug}: testing..."

tmp_dir=$(mktemp -d -t "exercism-verify-${slug}-XXXXX")

trap 'rm -rf "$tmp_dir"' EXIT
cp -r "${solution_dir}/." "${tmp_dir}"
cd "${tmp_dir}"
test_file="tests/test-${slug}.art"
sed -i -E 's/(test|it).skip/\1/g' "${test_file}"

# Run the Arturo tester, capturing output
echo "Running tests via Arturo..."
test_output=$(arturo tester.art 2>&1)



RUNNER_PATH="/opt/test-runner/src/test.py"
if [ ! -f "$RUNNER_PATH" ]; then
    # Fallback for local testing relative to bin/
    RUNNER_PATH="$(dirname "$0")/../src/test.py"
fi


python3 "$RUNNER_PATH" "${test_file}" ".unitt/tests/test-${slug}.art" "${test_output}"

if [ -f results.json ]; then
    # If status is error and message is null, replace with test_output
    jq --arg output "${test_output}" \
       'if .status == "error" and .message == null then .message = $output else . end' \
       results.json > results.tmp.json && mv results.tmp.json results.json
    
    mv results.json "${results_file}"
    echo "${slug}: done (results written)"
else
    echo "Error: results.json was not generated."
    exit 1
fi

