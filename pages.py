'''Package page:

Define various structured pages.

Page: a simple page, with a header, a footer, and the rest of the contents

StructuredPage: a collection of elements
CoverPage: a StructuredPage, with a second header and a title
'''

import re
import sys

import elements
import toc
import utils

class Page:
    '''A page, split into: header, content, footer.

    Attributes:
        - header: str, the header line
        - footer: str, the footer line
        - content: list of str, all the other lines
        - indent: int, the minimal amount of space for indented content

    header and footer are stripped. content starts and ends with non-empty
    lines. content lines are right stripped, and there is no left margin, i.e.
    spaces are removed from the left until there is at least one line with no
    spaces. indent is the smallest non-zero amount of space starting a line,
    after left margin removal.'''
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
        margin = indents[0] # the indent all lines have

        self.header = lines[header].lstrip()
        self.footer = lines[footer].lstrip()
        self.content = [line[margin:] for line in contentlines]
        self.indent = indents[1] - margin if 2 <= len(indents) else 0

class StructuredPage:
    '''A collection of elements making up the contents of a page.

    Attributes:
        - elements: list of various classes from the elements module, the
          contents of the page
        - footnotes: dict of int to elements.Text, the footnotes of the page
        - inelement: boolean, True if the last element was not explicitely
          closed and the next line may belong to it'''
    def __init__(self, page, tocmatcher, startline=0):
        '''Parameters:
            - page: Page, the page to parse
            - tocmatcher: toc.TOCMatcher, the TOCMatcher object
            - startline: int, optional (default: 0), amount of lines to skip
              from the beginning of page'''
        self.elements = list()
        self.inelement = False
        self.footnotes = dict()

        footnoteregex = re.compile(fr"^\s{{{page.indent},}}\d+\)\s\S")
        i = startline
        while i < len(page.content):
            line = page.content[i]
            if footnoteregex.match(line):
                break
            self.addline(line, page.indent, tocmatcher)
            i += 1
        footnotesbegin = i

        if footnotesbegin == len(page.content):
            return # no footnotes

        lastfootnote = None
        for line in page.content[footnotesbegin:]:
            if line:
                if footnoteregex.match(line):
                    footnote, text = line.split(maxsplit=1)
                    self.footnotes[footnote] = elements.Text(text)
                    lastfootnote = footnote
                else:
                    try:
                        self.footnotes[lastfootnote].addcontent(line)
                    except:
                        print(startline, footnotesbegin, len(page.content))
                        print(line)
                        raise

    def addline(self, line, indent, tocmatcher):
        '''addline(self, line): Add a line to the page.

        Parse the line and integrate it to the page, either by appending it to
        an existing element, or by building a new element.

        Parameters:
            - line: str, the line to parse and add
            - indent: int, the amount of indentation to expect for paragraphs
            - tocmatcher: toc.TOCMatcher, the TOCMatcher object'''
        if not line:
            self.inelement = False
            return
        splits = line.split(maxsplit=1)
        groups = utils.groupwords(line)
        if tocmatcher.match(line):
            # title
            if splits[0][0].isdigit():
                # numbered title
                self.elements.append(elements.Heading.fromnumberedtitle(line))
            else:
                self.elements.append(elements.Heading(1, line))
            self.inelement = False
            return
        if splits[0][0] in ("—",):
            self.elements.append(elements.UnorderedListItem(line))
            self.inelement = True
            return
        if indent != 0 and line[0].isdigit():
            # numbered paragraph, with number in left margin
            self.elements.append(elements.NumberedParagraph(line))
            self.inelement = True
            return
        if splits[0][:-1].isdigit() and splits[0][-1] == '.':
            self.elements.append(elements.OrderedListItem(line))
            self.inelement = True
            return
        if indent == 0 or line[:indent].isspace():
            if self.inelement and isinstance(self.elements[-1], elements.Text):
                # continuation of previous text element
                self.elements[-1].addcontent(line)
                return
            # new paragraph
            self.elements.append(elements.Paragraph(line))
            return

        print("Could not parse line", file=sys.stderr)
        print(line, file=sys.stderr)
        raise NotImplementedError

    def __repr__(self):
        return '\n'.join([f"{e.__class__.__name__:20}{e.content}"
                          for e in self.elements]
                         + [f"{n}\t{f.content}"
                            for n, f in self.footnotes.items()])

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
