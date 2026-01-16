from utils import find_closing_bracket, extract_named_block

def parse_source_file(source_text):
    """
    Parses the Arturo source file to find test definitions.
    Returns a list of test groups (describes), each containing a list of tests.
    """
    test_groups = []
    
    pos = 0
    while True:
        describe_block = extract_named_block(source_text, pos, 'describe ')
        if not describe_block:
            break
            
        group_name = describe_block['name']
        group_content = describe_block['content']
        
        tests = []
        inner_pos = 0
        while True:
            # Find both possibilities
            kw1 = 'it '
            kw2 = 'it.skip '
            
            # We need to peek to see which comes first
            idx1 = group_content.find(kw1, inner_pos)
            idx2 = group_content.find(kw2, inner_pos)
            
            if idx1 == -1 and idx2 == -1:
                break
                
            if idx1 != -1 and (idx2 == -1 or idx1 < idx2):
                keyword = kw1
            else:
                keyword = kw2
            
            test_block = extract_named_block(group_content, inner_pos, keyword)
            
            if not test_block:
                # Should not happen if find succeeded, unless malformed
                # Advance slightly to avoid infinite loop if malformed
                inner_pos += 1
                continue
                
            tests.append({
                "name": test_block['name'],
                "code": test_block['content'].strip()
            })
            inner_pos = test_block['end_index'] + 1
            
        if tests:
            test_groups.append({
                "name": group_name,
                "tests": tests
            })
            
        pos = describe_block['end_index'] + 1
        
    return test_groups

def parse_test_results(result_text):
    """
    Parses the Arturo test result file (which is an Arturo structure).
    
    Returns a dictionary where keys are (describe_name, test_name) tuples 
    and values are dictionaries containing {'passed': bool, 'output': str}.
    """
    # Locate the `specs` block which contains the test results
    specs_start = result_text.find('specs: [')
    if specs_start == -1:
        return {}
        
    start_bracket = result_text.find('[', specs_start)
    end_bracket = find_closing_bracket(result_text, start_bracket)
    
    specs_content = result_text[start_bracket+1:end_bracket]
    
    parsed_results = {}
    
    # Iterate through each Describe block in the specs
    pos = 0
    while True:
        # Find start of an object `#[ ... ]`
        obj_type_marker = specs_content.find('#[', pos)
        if obj_type_marker == -1: 
            break
            
        obj_start = specs_content.find('[', obj_type_marker)
        obj_end = find_closing_bracket(specs_content, obj_start)
        
        if obj_end == -1: 
            break
            
        # Extract the object content
        obj_content = specs_content[obj_start+1:obj_end]
        
        # Extract Description Name
        desc_start = obj_content.find('description: "')
        if desc_start != -1:
            q_start = desc_start + len('description: "')
            q_end = obj_content.find('"', q_start)
            describe_name = obj_content[q_start:q_end]
            
            # Find the nested `tests` list
            tests_start = obj_content.find('tests: [')
            if tests_start != -1:
                t_bracket_start = obj_content.find('[', tests_start)
                t_bracket_end = find_closing_bracket(obj_content, t_bracket_start)
                tests_list_content = obj_content[t_bracket_start+1:t_bracket_end]
                
                t_pos = 0
                while True:
                    t_obj_marker = tests_list_content.find('#[', t_pos)
                    if t_obj_marker == -1: 
                        break
                        
                    t_start = tests_list_content.find('[', t_obj_marker)
                    t_end = find_closing_bracket(tests_list_content, t_start)
                    
                    if t_end == -1: 
                        break
                        
                    test_content = tests_list_content[t_start+1:t_end]
                    
                    # Extract Test Name
                    td_start = test_content.find('description: "')
                    if td_start != -1:
                        td_q_start = td_start + len('description: "')
                        td_q_end = test_content.find('"', td_q_start)
                        test_name = test_content[td_q_start:td_q_end]
                        
                        # Extract Assertions
                        ass_start = test_content.find('assertions: [')
                        is_passed = False
                        assertion_code = None
                        
                        if ass_start != -1:
                            a_start = test_content.find('[', ass_start)
                            a_end = find_closing_bracket(test_content, a_start)
                            assertions_blob = test_content[a_start+1:a_end]
                            
                            assertions_found = False
                            all_passed = True
                            
                            ap_pos = 0
                            while True:
                                pair_start = assertions_blob.find('[', ap_pos)
                                if pair_start == -1: 
                                    break
                                pair_end = find_closing_bracket(assertions_blob, pair_start)
                                pair_text = assertions_blob[pair_start+1:pair_end]
                                
                                bool_val = None
                                if ' true' in pair_text or '\ntrue' in pair_text or '\ttrue' in pair_text:
                                    bool_val = True
                                elif ' false' in pair_text:
                                    bool_val = False
                                
                                if bool_val is not None:
                                    last_quote = pair_text.rfind('"')
                                    if last_quote != -1:
                                        first_quote = pair_text.find('"')
                                        if first_quote != -1 and first_quote < last_quote:
                                             raw_string = pair_text[first_quote+1:last_quote]
                                             if assertion_code is None:
                                                 assertion_code = raw_string
                                
                                    if bool_val is False:
                                        all_passed = False
                                        
                                    assertions_found = True
                                
                                ap_pos = pair_end + 1
                            
                            # Only add to results if assertions were actually found/executed
                            if assertions_found:
                                is_passed = all_passed
                                key = (describe_name.strip(), test_name.strip())
                                parsed_results[key] = {
                                    "passed": is_passed,
                                    "output": assertion_code
                                }
                    
                    t_pos = t_end + 1
                    
        pos = obj_end + 1
        
    return parsed_results
