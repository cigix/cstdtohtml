'''Package page:

Define various structured pages.

Page: a simple page, with a header, a footer, and the rest of the contents

StructuredPage: a collection of elements
CoverPage: a StructuredPage, with a second header and a title
'''

import re
import sys

import elements
import parser
import utils

class Page:
    '''A page, split into: header, content, footer.

    Attributes:
        - header: str, the header line
        - footer: str, the footer line
        - content: list of str, all the other lines
        - indent: int, columns of left margin

    header and footer are stripped. content starts and ends with non-empty
    lines. content lines are right stripped. indent is the number of columns at
    the beginning of all content lines where only paragraph numbering can be
    found.
    '''
    def __init__(self, page):
        '''
        Parameters:
            - page: str, the page'''
        lines = [line.rstrip() for line in page.split('\n')]
        header = 0
        while not lines[header]:
            header += 1
        footer = len(lines) - 1
        while not lines[footer]:
            footer -= 1

        contentbegin = header + 1
        while not lines[contentbegin]:
            contentbegin += 1
        contentend = footer - 1
        while not lines[contentend]:
            contentend -= 1

        contentlines = lines[contentbegin:contentend+1]

        indents = sorted(set(len(line) - len(line.lstrip())
                             for line in contentlines
                             if line))
        if indents[0] == 0 and len(indents) >= 2:
            # there are different indents, we need to find the maximal one such
            # that only paragraph numbers are under the indent
            def checkonlynumbersinmargin(lines, margin):
                if margin == 0:
                    return True

                for line in lines:
                    if line[:margin].strip():
                        try:
                            int(line[:margin])
                        except ValueError:
                            return False
                return True
            # initial estimation
            indent = indents[1]
            if checkonlynumbersinmargin(contentlines, indent):
                # the initial estimation is good, try to increase
                indent += 1
                while checkonlynumbersinmargin(contentlines, indent):
                    indent += 1
                indent -= 1
            else:
                # the initial estimation is not good, try to decrease
                while (indent > 0
                       and not checkonlynumbersinmargin(contentlines, indent)):
                    indent -= 1
            self.indent = indent
        else:
            # everything is indented, so there is no left margin
            self.indent = 0

        self.header = lines[header].lstrip()
        self.footer = lines[footer].lstrip()
        self.content = contentlines

class StructuredPage:
    '''A collection of elements making up the contents of a page.

    Attributes:
        - elements: list of various classes from the elements module, the
          contents of the page
        - footnotes: dict of int to list of various classes from the elements
          module, the footnotes of the page'''
    def __init__(self, page, tocmatcher, startline=0):
        '''Parameters:
            - page: Page, the page to parse
            - tocmatcher: toc.TOCMatcher, the TOCMatcher object
            - startline: int, optional (default: 0), amount of lines to skip
              from the beginning of page'''
        footnoteregex = re.compile(fr"^\s+\d+\)\s\S")
        lineparser = parser.LineParser(page.indent)
        i = startline
        while i < len(page.content):
            line = page.content[i]
            if footnoteregex.match(line):
                break
            lineparser.parseline(line, tocmatcher)
            i += 1
        footnotesbegin = i

        self.elements = lineparser.elements
        self.footnotes = dict()

        if footnotesbegin == len(page.content):
            return # no footnotes

        footnotes = dict() # int to parser
        lastfootnote = None
        for line in page.content[footnotesbegin:]:
            try:
                if footnoteregex.match(line):
                    footnote, text = line.split(maxsplit=1)
                    try:
                        footnote = int(footnote[:-1])
                    except ValueError:
                        print("Could not parse footnote number",
                              file=sys.stderr)
                        raise
                    footnotes[footnote] = parser.LineParser(page.indent)
                    footnotes[footnote].parseline(text, tocmatcher, 0)
                    lastfootnote = footnote
                else:
                    footnotes[lastfootnote].parseline(line, tocmatcher)
            except:
                print(footnotes)
                print(line, sys.stderr)
                raise

        for f, p in footnotes.items():
            self.footnotes[f] = p.elements

    def __repr__(self):
        elements = '\n'.join(f"{e.__class__.__name__:25}{e}"
                             for e in self.elements)
        footnotes = (str(f)
                     + ')\t'
                     + '\n\t'.join(f"{e.__class__.__name__:17}{e}" for e in l)
                     for f, l in self.footnotes.items())
        return elements + '\n' + '\n'.join(footnotes)

    def reindentcodes(self):
        '''reindentcodes(self): Rework the indentation of the code blocks.

        Remove spaces that are present at the beginning of all lines.'''
        for e in self.elements:
            if isinstance(e, elements.Code):
                indents = [len(l) - len(l.lstrip())
                           for l in e.lines
                           if l]
                margin = min(indents)
                newlines = [l[margin:] for l in e.lines]
                e.lines = newlines

class CoverPage(StructuredPage):
    '''A piece of content preceded by a subheader and a title.

    Attributes:
        - subheader: list of str, the second header
        - title: str, the title line
        - see StructuredPage'''
    def __init__(self, page, tocmatcher):
        '''Parameters:
            - page: Page, the page to parse
            - tocmatcher: toc.TOCMatcher, the TOCMatcher object'''
        subheaderline = 0
        while not page.content[subheaderline]:
            subheaderline += 1
        titleline = subheaderline + 1
        while not page.content[titleline]:
            titleline += 1

        self.subheader = utils.groupwords(page.content[subheaderline])
        self.title = page.content[titleline].strip()
        StructuredPage.__init__(self, page, tocmatcher, titleline + 1)
