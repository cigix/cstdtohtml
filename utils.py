'''Package utils:

Contains definitions shared across multiple packages.'''

def groupwords(string):
    '''groupwords(string): Split a string into groups of words.

    Return a list of all substrings containing only single spaces.'''
    # Split by multiple spaces, remove empty groups, remove leading spaces.
    return list(map(str.lstrip, filter(None, string.split("  "))))

def isint(string):
    '''isint(string): Check if string could be parsed as int.'''
    try:
        int(string)
    except ValueError:
        return False
    else:
        return True
