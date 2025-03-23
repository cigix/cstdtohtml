'''Package page:

Define various structured pages.

Page: a simple page, with a header, a footer, and the rest of the contents

StructuredPage: a collection of elements
CoverPage: a StructuredPage, with a second header and a title
'''

import copy
import re
import sys

import elements
import parser
import utils

class Page:
    '''A page, split into: header, content, footer.

    Attributes:
        - header: list of str, the header lines
        - footer: list of str, the footer lines
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

        # headerbegin: first non-empty line of header
        # headerend: first empty line after header
        headerbegin = 0
        while not lines[headerbegin]:
            headerbegin += 1
        headerend = headerbegin + 1
        while lines[headerend]:
            headerend += 1

        # footerbegin: first non-empty line of footer
        # footerend: first empty line after footer
        footerend = len(lines)
        while not lines[footerend - 1]:
            footerend -= 1
        footerbegin = footerend - 1
        while lines[footerbegin - 1]:
            footerbegin -= 1

        # contentbegin: first non-empty line after header
        # contentend: first empty line before footer
        contentbegin = headerend + 1
        while not lines[contentbegin]:
            contentbegin += 1
        contentend = footerbegin - 1
        while not lines[contentend - 1]:
            contentend -= 1

        contentlines = lines[contentbegin:contentend]

        indents = sorted(set(len(line) - len(line.lstrip())
                             for line in contentlines
                             if line))
        if 2 <= len(indents) and indents[0] == 0:
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

        self.header = [line.lstrip() for line in lines[headerbegin:headerend]]
        self.footer = [line.lstrip() for line in lines[footerbegin:footerend]]
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
        footnoteregex = re.compile(r"^\s+\d+\)\s?\S")
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
                    footnote, text = line.split(')', maxsplit=1)
                    try:
                        footnote = int(footnote)
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
        elementstr = '\n'.join(f"{e.__class__.__name__:25}{e}"
                               for e in self.elements)
        footnotestrs = (str(f)
                        + ')\t'
                        + '\n\t'.join(f"{e.__class__.__name__:17}{e}"
                                      for e in l)
                        for f, l in self.footnotes.items())
        return elementstr + '\n' + '\n'.join(footnotestrs)

    def reindentcodes(self):
        '''reindentcodes(self): Rework the indentation of code blocks.

        Remove spaces that are present at the beginning of all lines in a code
        block.'''
        def reindentlines(lines):
            indents = [len(l) - len(l.lstrip())
                       for l in lines
                       if l]
            margin = min(indents)
            return [l[margin:] for l in lines]

        for e in self.elements:
            if isinstance(e, elements.Code):
                e.lines = reindentlines(e.lines)
        for footnote, elems in self.footnotes.items():
            for i, elem in enumerate(elems):
                if isinstance(elem, elements.Code):
                    self.footnotes[footnote][i].lines = (
                        reindentlines(elem.lines))

    def reworkfootnotes(self):
        '''reworkfootnotes(self): Rework the elements of footnotes.

        Footnotes usually have weird indentation and extraneous empty lines,
        which may lead to weird parsing. Instead of having specific parsing
        rules for footnotes, we parse them just like usual content, and fix them
        with this method.'''
        for footnote in self.footnotes.keys():
            if self.footnotes[footnote]:
                # remove extraneous spacing between the first two words
                if isinstance(self.footnotes[footnote][0], elements.Paragraph):
                    splits = (self.footnotes[footnote][0]
                              .content.split(maxsplit=1))
                    if len(splits) == 2:
                        self.footnotes[footnote][0] = (
                            elements.Paragraph(' '.join(splits)))
                    else: # only one word in the first paragraph, that's fishy
                        if isinstance(self.footnotes[footnote][1],
                                      elements.Code):
                            lines = self.footnotes[footnote][1].lines
                            # avoid extra newline with the first line
                            self.footnotes[footnote][0].content += (' '
                                                                    + lines[0])
                            # turn the other lines into paragraphs, they'll get
                            # sorted out later on
                            newpars = list()
                            for line in lines[1:]:
                                newpars.append(elements.Paragraph(line))
                            # replace the Code with the Paragraphs
                            self.footnotes[footnote][1:2] = newpars
                elif isinstance(self.footnotes[footnote][0],
                                elements.ValueDefinition):
                    newparcontent = (
                        self.footnotes[footnote][0].value
                        + ' '
                        + self.footnotes[footnote][0].content)
                    newpar = elements.Paragraph(newparcontent)
                    self.footnotes[footnote][0] = newpar

                # Merge consecutive paragraphs
                newelems = list()
                islastaparagraph = False
                for elem in self.footnotes[footnote]:
                    if isinstance(elem, elements.Paragraph):
                        if islastaparagraph:
                            newelems[-1].addcontent(elem.content)
                        else:
                            newelems.append(elem)
                            islastaparagraph = True
                    elif (islastaparagraph
                          and isinstance(elem, elements.UnorderedListItem)):
                        # An U+2014 EM DASH has been mistaken for a list item
                        newelems[-1].addcontent("— " + elem.content)
                    else:
                        newelems.append(elem)
                        islastaparagraph = False
                self.footnotes[footnote] = newelems

    def fixfootnoterefs(self):
        '''fixfootnoterefs(self): Fix the contents for a known pattern.

        Sometimes footnote references appear on their separate line above the
        line they should be on:

                       123)
            lorem ipsum

        instead of:

            lorem ipsum123)

        This causes the footnote reference to be considered as code, and so does
        the following line.'''
        todelete = list()
        for i in range(1, len(self.elements)):
            if not isinstance(self.elements[i], elements.Code):
                continue
            code = self.elements[i]
            if not len(code.lines) >= 2:
                continue
            if not (utils.isint(code.lines[0][:-1])
                    and code.lines[0][-1] == ')'):
                continue
            if not isinstance(self.elements[i - 1], elements.Text):
                continue
            prevtext = self.elements[i - 1]
            firstline = code.lines[1] + code.lines[0].lstrip()
            prevtext.addcontent(firstline)
            for line in code.lines[2:]:
                prevtext.addcontent(line)
            todelete.append(i)

        for i in reversed(todelete):
            self.elements[i:i+1] = []

    def _putfootnoteplaceholder(self, footnote):
        regex = re.compile(fr"{footnote}\)")
        placeholder = f"\x1bfootnote{footnote}\x1b"
        for elem in self.elements:
            if isinstance(elem, elements.Code):
                for i in range(len(elem.lines)):
                    elem.lines[i], n = regex.subn(placeholder, elem.lines[i])
                    if 0 < n:
                        elem.footnotes.add(footnote)
            elif isinstance(elem, elements.Text):
                if elem.content[:20] == "Forward references: ":
                    # contains a lot of sequences of the form "<number>)" that
                    # are never footnotes
                    continue
                elem.content, n = regex.subn(placeholder, elem.content)
                if 0 < n:
                    elem.footnotes.add(footnote)

    def putfootnoteplaceholders(self):
        r'''putfootnoteplaceholders(self): Replace footnote references with
        placeholders.

        Match the footnotes with the contents of the page, replacing the
        references ("<number>)") with placeholders
        ("\x1bfootnote<number>\x1b"). Also registers them to the elements'
        footnote field where applicable.'''
        for footnote in self.footnotes.keys():
            self._putfootnoteplaceholder(footnote)

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

def mergepages(pages):
    '''mergepages(pages): Get a single long page from individual pages.

    Parameters:
        - pages: list of StructuredPage, the pages to merge

    Return: type(pages[0]), the merged pages.'''
    merge = copy.deepcopy(pages[0])
    for page in pages[1:]:
        # Is there a chance an element was split over two pages?
        # A Code (any subclass) plus a Code (strict)
        if (isinstance(merge.elements[-1], elements.Code)
                and type(page.elements[0]) is elements.Code):
            cutcode = page.elements.pop(0)
            merge.elements[-1].lines += cutcode.lines
            merge.elements[-1].footnotes |= cutcode.footnotes
        # A Text (any subclass) plus a Paragraph (strict) starting with a
        # lowercase
        elif (isinstance(merge.elements[-1], elements.Text)
                and type(page.elements[0]) is elements.Paragraph
                and page.elements[0].content[0].islower()):
            cuttext = page.elements.pop(0)
            merge.elements[-1].addcontent(cuttext.content)
            merge.elements[-1].footnotes |= cuttext.footnotes
        # A ValueDefinition (any subclass) plus a Code (strict)
        elif (isinstance(merge.elements[-1], elements.ValueDefinition)
                and type(page.elements[0]) is elements.Code):
            cutcode = page.elements.pop(0)
            for line in cutcode.lines:
                merge.elements[-1].addcontent(line)
            merge.elements[-1].footnotes |= cutcode.footnotes

        merge.elements += page.elements
        for footnote, elems in page.footnotes.items():
            if footnote in merge.footnotes:
                raise KeyError(f"Footnote present multiple times: {footnote}")
            merge.footnotes[footnote] = elems
    return merge
