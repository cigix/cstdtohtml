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
    '''A tool to match TOC entries and headings in the contents

    This object helps identify the headings in the content, whether because they
    are referenced in the TOC, or because they are a subheading of the last
    matched entry from the TOC.'''
    def __init__(self, toc):
        '''Parameters:
            - toc: TOC, the table of contents'''
        def maketitleregex(title, key):
            if key is None:
                return re.compile(fr"^\s{{4}}{title}$")
            if key.count('.') == 0:
                return re.compile(fr"^\s{{4}}{key}\.\s+{title}$")
            return re.compile(fr"^\s{{4}}{key}\s+{title}$")

        self._titlestack = [maketitleregex(t, k)
                            for t, k in reversed(toc.titles)]

        def makeheadingregex(key):
            if key is None:
                return None
            return re.compile(fr"^\s{{4}}{key}(\.\d+)+$")

        self._headingstack = [makeheadingregex(k)
                              for _, k in reversed(toc.titles)]
        # At the beginning, before any title has been matched, we shall not
        # match against any heading
        self._headingstack += [None]

    def matchtitle(self, line):
        '''matchtitle(self, line): Match a line against the next TOC entry.

        Parameters:
            - line: str, the line to match

        Return: bool, True if the line matched

        ⚠️ This function modifies the object. Consequent calls with similar
        inputs may not give the same output.⚠️

        Only the top entry is matched. If the match is successful, the entry is
        removed from the stack.'''
        if self._titlestack:
            if self._titlestack[-1].fullmatch(line):
                self._titlestack.pop()
                self._headingstack.pop()
                return True
        return False

    def matchheading(self, line):
        '''matchheading(self, line): Match a line under the latest TOC entry.

        Parameters:
            - line: str, the line to match

        Return: bool, True if the line matched

        Only the top entry is matched.'''
        if self._headingstack and self._headingstack[-1] is not None:
            if self._headingstack[-1].fullmatch(line):
                return True
        return False
