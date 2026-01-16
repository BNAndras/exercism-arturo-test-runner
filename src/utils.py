
def find_closing_bracket(text, start_index):
    """
    Finds the index of the matching closing bracket ']' for the opening bracket '['
    at text[start_index].
    
    Returns -1 if no matching bracket is found.
    """
    depth = 0
    for i in range(start_index, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                return i
    return -1

def extract_named_block(text, start_search_pos, keyword):
    """
    Helper to extract a block like: keyword "name" [ ... ]
    
    Returns a dictionary with:
    - name: The string inside quotes
    - content: The content inside the brackets
    - end_index: The index where the block ends
    
    Returns None if the keyword is not found.
    """
    keyword_index = text.find(keyword, start_search_pos)
    if keyword_index == -1:
        return None
        
    # Find the name (string inside quotes)
    quote_start = text.find('"', keyword_index) + 1
    quote_end = text.find('"', quote_start)
    name = text[quote_start:quote_end]
    
    # Find the content block
    block_start = text.find('[', quote_end)
    block_end = find_closing_bracket(text, block_start)
    
    if block_end == -1:
        return None
        
    return {
        "name": name,
        "content": text[block_start + 1:block_end],
        "end_index": block_end
    }
