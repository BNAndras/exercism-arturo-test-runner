import sys
import json
from pathlib import Path
from parsers import parse_source_file, parse_test_results

def main():
    if len(sys.argv) < 2: 
        print("Usage: python test.py <test-file.art> [result-file.art]")
        return
    
    source_path = Path(sys.argv[1])
    
    try:
        source_text = source_path.read_text(encoding='utf-8')
        test_definitions = parse_source_file(source_text)
    except FileNotFoundError:
        print(f"Error: Source file {source_path} not found.", file=sys.stderr)
        sys.exit(1)

    result_path = None
    if len(sys.argv) >= 3:
        result_path = Path(sys.argv[2])
    else:
        candidates = [
            source_path.parent / ".unitt" / "tests" / source_path.name,
            Path(".unitt") / "tests" / source_path.name
        ]
        for c in candidates:
            if c.exists():
                result_path = c
                break
                
    if not result_path or not result_path.exists():
        print("Error: No result file found.", file=sys.stderr)
        pass

    results_text = ""
    if result_path and result_path.exists():
        print(f"Reading results from {result_path}")
        results_text = result_path.read_text(encoding='utf-8')
    
    test_results = parse_test_results(results_text)
    
    # Check for optional execution output (stdout/stderr captured by runner)
    execution_output = None
    if len(sys.argv) >= 4:
        execution_output = sys.argv[3]
    
    v2_tests = []
    global_status = "pass"
    
    has_tests_defined = any(group['tests'] for group in test_definitions)
    if has_tests_defined and not test_results:
        final_output = {
            "version": 2,
            "status": "error",
            "message": execution_output, 
            "tests": []
        }
        write_output(final_output)
        return

    for group in test_definitions:
        group_name = group['name'].strip()
        
        for test in group['tests']:
            test_name = test['name'].strip()
            test_code = test['code']
            
            test_obj = {
                "name": test_name,
                "test_code": test_code,
                "status": "pass",
                "message": None
            }
            
            key = (group_name, test_name)
            
            if key in test_results:
                result = test_results[key]
                if not result['passed']:
                    test_obj['status'] = 'fail'
                    assertion_val = result['output']
                    
                    if assertion_val and test_code.startswith("expects.be:'"):
                        test_obj['message'] = f"expects.be:'{assertion_val}"
                    else:
                        test_obj['message'] = assertion_val if assertion_val else "Assertion failed"
                        
                    if global_status != "error":
                        global_status = "fail"
            else:
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
    write_output(final_output, global_status)

def write_output(data, status_log=""):
    output_file = Path("results.json")
    output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"Written output to {output_file.resolve()}. Status: {status_log}")

if __name__ == "__main__":
    main()