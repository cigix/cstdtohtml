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
