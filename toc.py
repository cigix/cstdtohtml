'''Package toc:

TOC stores various information about the table of contents.'''

import re
import utils

ANNEXREGEX = r"[A-Z]\b"
CHAPTERREGEX = r"\d+"
KEYREGEX = fr"(?:(?:{CHAPTERREGEX})|(?:{ANNEXREGEX}))(?:\.\d+)+"
PAGENUMREGEX = r"[0-9ivx]+"
TITLEREGEX = r"\w(?:[^ .][ .]?)+[^ .]"

UNKEYEDCHAPTERRE = re.compile(fr"({TITLEREGEX})\s+({PAGENUMREGEX})")
CHAPTERRE = re.compile(fr"({CHAPTERREGEX})\s+({TITLEREGEX})\s+({PAGENUMREGEX})")
SECTIONRE = re.compile(fr"\s*({KEYREGEX})\s+({TITLEREGEX})\s+(?:\. )*\s*({PAGENUMREGEX})")

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
                if m := UNKEYEDCHAPTERRE.fullmatch(line):
                    title, page = m.groups()
                    self.titles.append((title, None))
                elif m := CHAPTERRE.fullmatch(line):
                    key, title, page = m.groups()
                    self.titles.append((title, key))
                elif m := SECTIONRE.fullmatch(line):
                    key, title, page = m.groups()
                    self.titles.append((title, key))
                else:
                    print("Unrecognized TOC pattern:", repr(line))
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
                if title[:6] == "Annex ":
                    return re.compile(fr"^\s+{title[:7]}$")
                return re.compile(fr"^\s*{title}$")
            if key.count('.') == 0:
                return re.compile(fr"^\s*{key}\.\s+{title}$")
            return re.compile(fr"^\s*{key}\s+{title}$")

        self._titlestack = [maketitleregex(t, k)
                            for t, k in reversed(toc.titles)]

        def makeheadingregex(key):
            if key is None:
                return None
            return re.compile(fr"^\s*{key}(\.\d+)+($|\s)")

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
            if self._headingstack[-1].match(line):
                # Fix N3220 6.7.3.1p5: it is not a title, just unfortunate
                # reference
                if line.startswith('6.7.3.2 through 6.7.3.6'):
                    return False
                return True
        return False
