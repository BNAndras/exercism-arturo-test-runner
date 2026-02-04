import re
import sys
import json
from pathlib import Path

from parsing_test_describes import parse_source_file
from parsing_test_results import parse_test_results

def main():
    """
    Main entry point for the Python Test Runner (Parser).
    
    Usage: python parser.py <test-file.art> [result-file.art] [execution-output]
    """
    if len(sys.argv) < 2: 
        print("Usage: python parser.py <test-file.art> [result-file.art] [execution-output]")
        return
    
    source_path = Path(sys.argv[1])
    
    try:
        source_text = source_path.read_text(encoding='utf-8')
        test_definitions = parse_source_file(source_text)
    except FileNotFoundError:
        print(f"Error: Source file {source_path} not found.", file=sys.stderr)
        sys.exit(1)

    result_path = resolve_result_path(source_path)
    
    results_text = ""
    if result_path and result_path.exists():
        results_text = result_path.read_text(encoding='utf-8')
    else:
        print("Error: No result file found.", file=sys.stderr)
    
    test_results = parse_test_results(results_text)
    
    execution_output = None
    if len(sys.argv) >= 4:
        execution_output = sys.argv[3]
    
    final_output, global_status = build_output(test_definitions, test_results, execution_output)
    
    write_output(final_output)


def resolve_result_path(source_path: Path) -> Path | None:
    """
    Determines the path to the expected result file.
    """
    if len(sys.argv) >= 3:
        return Path(sys.argv[2])
    
    # Defaults
    candidates = [
        source_path.parent / ".unitt" / "tests" / source_path.name,
        Path(".unitt") / "tests" / source_path.name
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def build_output(
    test_definitions: list[dict[str, object]], 
    test_results: dict, 
    execution_output: str | None
) -> tuple[dict[str, object], str]:
    """
    Constructs the Exercism v2 JSON output structure.
    """
    v2_tests = []
    global_status = "pass"
    
    if test_definitions and not test_results:
        return {
            "version": 2,
            "status": "error",
            "message": normalize_output(execution_output), 
            "tests": []
        }, "error"

    for test in test_definitions:
        suite_name = test['suite'].strip() if test['suite'] else None
        test_name = test['name'].strip()
        test_code = test['code']
        
        test_obj = {
            "name": test_name,
            "test_code": test_code,
            "status": "pass",
            "message": None
        }
        
        test_key = (suite_name, test_name)
        
        if test_key in test_results:
            result = test_results[test_key]
            if not result['passed']:
                mark_as_failed(test_obj, result['output'], test_code)
                if global_status != "error":
                    global_status = "fail"
        else:
            # Fallback: if suite_name mismatch or missing, we can't easily map
            test_obj['status'] = 'error'
            test_obj['message'] = "Test was not found in validation results."
            if global_status != "error":
                global_status = "fail"
        
        v2_tests.append(test_obj)

    final_output = {
        "version": 2,
        "status": global_status,
        "tests": v2_tests
    }
    return final_output, global_status


def mark_as_failed(test_obj: dict[str, object], assertion_val: str | None, test_code: str):
    """
    Updates the test object with failure status and message.
    """
    test_obj['status'] = 'fail'
    
    msg = None
    if assertion_val and test_code.startswith("expects.be:'"):
        # Helper to construct a meaningful message mimicking assertion code
        msg = f"expects.be:'{assertion_val}"
    else:
        msg = assertion_val if assertion_val else "Assertion failed"
    
    test_obj['message'] = normalize_output(msg)

def normalize_output(text: str | None) -> str | None:
    """
    Normalizes command line output to ensure consistency between environments 
    (Local vs Docker) by sanitizing paths and terminal width artifacts.
    """
    if not text:
        return text
        
    # Regex to sanitize absolute paths to a fixed placeholder (e.g. ~/.arturo/...)
    # Matches: /any/absolute/path/.arturo -> ~/.arturo
    # Also handles the specific /root/ case for Docker
    # We strip any path component ending in /.arturo/
    text = re.sub(r'/[^ \n"]+/\.arturo/', '~/.arturo/', text)
    
    # Normalize the error header line to fixed width
    # Example: ══╡ Name Error ╞════════════ <script> ══
    text = re.sub(r'╞═+.*? <script> ══', '╞════════════════════════════════════════════════════ <script> ══', text)
    
    return text

def write_output(data: dict[str, object]):
    """Writes the v2 test results to JSON."""
    output_file = Path("results.json")
    try:
        output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding='utf-8')
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()