import pyparsing
import textwrap

from parsing_common import regular_block, string_value, search_all


describe_keyword = pyparsing.Keyword("describe")
it_keyword = pyparsing.Literal("it.skip") | pyparsing.Keyword("it")

# 'describe' block: describe "Name" [ content ] 
describe_block = describe_keyword + string_value("name") + regular_block("content")

# 'it' block: it "Name" [ code ] (or it.skip)
test_block = it_keyword("type") + string_value("name") + regular_block("code")


item_grammar = describe_block | test_block

def extract_tests(text: str, current_suite: str | None) -> list[dict[str, object]]:
    """
    Recursively extracts tests from text in order, assigning them to their immediate suite.
    Returns: list of test dicts with keys: name, code, suite.
    """
    tests = []
    
    # scan_string finds non-overlapping matches in order
    for match, start, end in item_grammar.scan_string(text):
        if "content" in match: # Describe block
            group_name = match["name"]
            content = match["content"]
            
            # Recurse into the describe block, passing it as the new suite
            nested_tests = extract_tests(content, group_name)
            tests.extend(nested_tests)
        
        elif "code" in match: # Test block
            raw_code = match["code"]
            stripped_code = raw_code.strip("\n") 
            dedented_code = textwrap.dedent(stripped_code).strip()
            
            tests.append({
                "name": match["name"],
                "code": dedented_code,
                "suite": current_suite
            })
            
    return tests


def parse_source_file(source_text: str) -> list[dict[str, object]]:
    """
    Parses the Arturo source file to find test definitions.
    Returns a flattened list of tests in source order.
    """
    # We assume top-level tests might exist, or everything is in a describe.
    # We start with None as suite. 
    # BUT: The top-level describe in 'misc-multiple-describes' is "Misc Multiple Describes".
    # The tests inside it ("Inner Describe") are children.
    # If we pass None, the top block "Misc..." will be found.
    # Recursion will pass "Misc..." as suite to its children.
    return extract_tests(source_text, None)
