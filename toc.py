'''Package toc:

TOC stores various information about the table of contents.'''

import re
import utils

ANNEXREGEX = r"[A-Z]\b"
CHAPTERREGEX = r"\d+"
KEYREGEX = fr"(({CHAPTERREGEX})|({ANNEXREGEX}))(\.\d+)+"

class TOC:
    '''A representation of the table of contents.

    Attributes:
        - titleline: str, the title line
        - titles: list of tuple (str, None or str), the association of title and
          key; some titles have no key

    Some titles are duplicate.'''
    def __init__(self, tocpages):
        '''Parameters:
            - tocpages: list of page.Page, the TOC pages'''
        contents = sum(map((lambda p: p.content), tocpages), start=[])
        self.titleline = contents[0]
        self.titles = list()
        for line in contents[1:]:
            if not line:
                continue
            try:
                splits = line.split(maxsplit=1)
                if re.fullmatch(KEYREGEX, splits[0]):
                    # numbered title, with dots
                    key = splits[0]
                    title = splits[1].split(' .', maxsplit=1)[0]
                    self.titles.append((title, key))
                else:
                    groups = utils.groupwords(line)
                    if groups[0][0].isdigit():
                        # numbered title, no dots
                        self.titles.append((groups[1], groups[0]))
                    else:
                        self.titles.append((groups[0], None))
            except:
                print(line)
                raise

class TOCMatcher:
    '''A tool to match TOC entries in the contents'''
    def __init__(self, toc):
        '''Parameters:
            - toc: TOC, the table of contents'''
        def makeregex(title, key):
            if key is None:
                return fr"^\s{{4}}{title}$"
            if key.count('.') == 0:
                return fr"^\s{{4}}{key}\.\s+{title}$"
            return fr"^\s{{4}}{key}\s+{title}$"
        self._tomatchstack = [re.compile(makeregex(t, k))
                              for t, k in reversed(toc.titles)]

    def match(self, line):
        '''match(self, line): Match a line against the next TOC entry.

        Parameters:
            - line: str, the line to match

        Return: bool, True if the line matched

        ⚠️ This function modifies the object. Consequent calls with similar
        inputs may not give the same output.⚠️

        Only the top entry is matched. If the match is successful, the entry is
        removed from the stack.'''
        if self._tomatchstack:
            if self._tomatchstack[-1].fullmatch(line):
                self._tomatchstack.pop()
                return True
        return False
