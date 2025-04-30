'''Package linker:

Identify references in the contents.'''

import re

import elements
import toc

# level 0 regex: too broad, needs context
LEVEL0 = fr"{toc.ANNEXREGEX}|{toc.CHAPTERREGEX}"
# level 1 regex: likely a reference, but could be a floating point number
LEVEL1 = fr"(?:{LEVEL0})(?:\.\d+)"
# level 2 regex: unlikely not a reference
LEVEL2 = fr"(?:{LEVEL1})(?:\.\d+)+"

# Note that some level 2s may not be referenced in the TOC.

# What to link:
# - in "Forward references: " paragraphs: any KEYREGEX
# - http links
# - any LEVEL2
# - "clause CHAPTERREGEX"
# - "clauses CHAPTEREGEX-CHAPTERREGEX"
# - "annex ANNEXREGEX"
# - "[LEVEL1]"
# - " (LEVEL1)"
# - "see LEVEL1"
# - "by LEVEL1"
# - "in LEVEL1"
# - "subclause LEVEL1", "Subclause LEVEL1"

def putlinksplaceholders(elems):
    r'''putlinksplaceholders(elems): Identify links and replace them with
    placeholders.

    Parameters:
        - elems: list of objects, the elements to link

    Linking happens inplace, and only on elements.Text instances. Placeholders
    are of the form "\x1blink<contents>\x1b".'''
    placeholder0 = "\x1blink\\g<0>\x1b" # link whole match
    placeholder2 = "\\g<1>\x1blink\\g<2>\x1b" # keep group 1, link group 2
    # keep groups 1 and 3, link group 2
    placeholder3 = "\\g<1>\x1blink\\g<2>\x1b\\g<3>"
    # keep groups 1 and 3, link groups 2 and 4
    placeholder4 = "\\g<1>\x1blink\\g<2>\x1b\\g<3>\x1blink\\g<4>\x1b"
    # Simple http url regex. Fancier means more universal means more wrong
    # matches.
    http = re.compile("https?://[-a-zA-Z0-9_/.]+[a-zA-Z0-9_/]")
    key = re.compile(toc.KEYREGEX)
    level2 = re.compile(LEVEL2)
    clause = re.compile(fr"(clause\s)({toc.CHAPTERREGEX})")
    clauses = re.compile(
        fr"(clauses\s)({toc.CHAPTERREGEX})(–)({toc.CHAPTERREGEX})")
    annex = re.compile(fr"(annex\s)({toc.ANNEXREGEX})")
    squarebrackets = re.compile(fr"(\[)({LEVEL1})(\])")
    roundbrackets = re.compile(fr"(\s\()({LEVEL1})(\))")
    seebyin = re.compile(fr"((?:see|by|in)\s)({LEVEL1})")
    subclause = re.compile(fr"([Ss]ubclause\s)({LEVEL1})")
    def dosubstitutions(string):
        string = http.sub(placeholder0, string)
        string = level2.sub(placeholder0, string)
        string = clause.sub(placeholder2, string)
        string = clauses.sub(placeholder4, string)
        string = annex.sub(placeholder2, string)
        string = squarebrackets.sub(placeholder3, string)
        string = roundbrackets.sub(placeholder3, string)
        string = seebyin.sub(placeholder2, string)
        string = subclause.sub(placeholder2, string)
        return string

    for element in elems:
        if isinstance(element, elements.Code):
            for i in range(len(element.lines)):
                element.lines[i] = dosubstitutions(element.lines[i])
        if not isinstance(element, elements.Text):
            continue
        if element.content[:20] == "Forward references: ":
            element.content = key.sub(placeholder0, element.content)
            continue
        element.content = dosubstitutions(element.content)
