'''Package parser:

Defines LineParser, an object that turns lines into elements.'''

import sys

import elements
import utils

class LineParser:
    '''An aggregator of lines that turns them into elements.

    Attributes:
        - elements: list of various classes from the elements module, the
          parsed lines'''
    def __init__(self, indent):
        '''Parameters:
            - indent: int, the amount of indentation to expect for paragraphs'''
        self.elements = list()
        # Should new text be appended to the last element?
        self._inelement = False
        self._indent = indent

    def _parselinewithoutindent(self, line, tocmatcher):
        splits = line.split(maxsplit=1)
        groups = utils.groupwords(line)
        if line[:20] == "Forward references: ":
            # make it its own paragraph
            self.elements.append(elements.Paragraph(line))
            self._inelement = True
            return
        #print(tocmatcher._titlestack[-1], tocmatcher._headingstack[-1], line, sep='\t')
        if tocmatcher.matchtitle(line):
            if splits[0][0].isdigit():
                # numbered title
                self.elements.append(elements.NumberedTitleHeading(line))
            else:
                # title
                self.elements.append(elements.TitleHeading(line))
            self._inelement = False
            return
        if tocmatcher.matchheading(line):
            if len(splits) == 2:
                # numbered title
                self.elements.append(elements.NumberedTitleHeading(line))
            else:
                # heading
                self.elements.append(elements.NumberedHeading(line))
            self._inelement = False
            return
        if splits[0][0] in ("—", '•'):
            # list element
            self.elements.append(elements.UnorderedListItem(line))
            self._inelement = True
            return
        #print(splits, line)
        if splits[0][:-1].isdigit() and splits[0][-1] == '.':
            # ordered list
            self.elements.append(elements.OrderedListItem(line))
            self._inelement = True
            return
        if utils.isint(line[:8]):
            # value definition
            self.elements.append(elements.ValueDefinition(line))
            self._inelement = True
            return
        if line[0] == '−' and utils.isint(line[1:8]):
            # value definition, but with an unparsable − U+2212 MINUS SIGN
            # instead of - U+002D HYPHEN-MINUS
            self.elements.append(elements.ValueDefinition(line.replace('−',
                                                                       '-')))
            self._inelement = True
            return
        if line[:4].isspace():
            # indented
            if self._inelement:
                # maybe it's part of the previous element ?
                def maybepreviouselement(previouselement):
                    if isinstance(previouselement, elements.Code):
                        return True
                    if isinstance(previouselement, elements.ValueDefinition):
                        return True
                    if (isinstance(previouselement, elements.UnorderedListItem)
                        and previouselement.level > 1):
                        return True
                    return False
                if maybepreviouselement(self.elements[-1]):
                    self.elements[-1].addcontent(line)
                    return
            if (self.elements
                and isinstance(self.elements[-1], elements.UnorderedListItem)
                and self.elements[-1].level > 1):
                # indented paragraph, inside a list
                self.elements.append(elements.Paragraph(line))
                self._inelement = True
                return
            if line[:7].isspace():
                # code block
                # we already checked for _inelement
                self.elements.append(elements.Code(line))
                self._inelement = True
                return
            # idk, make it a paragraph

        # regular text
        if self._inelement and isinstance(self.elements[-1], elements.Text):
            # continuation of previous text element
            self.elements[-1].addcontent(line)
            return
        # new paragraph
        self.elements.append(elements.Paragraph(line))
        self._inelement = True
        return

    def _parselinewithindent(self, line, indent, tocmatcher):
        if line[:indent].isspace():
            #print(f"{indent}\t|{line[indent:]}")
            return self._parselinewithoutindent(line[indent:], tocmatcher)
        try:
            num = int(line[:indent])
        except:
            print(f"Could not parse indent of {indent}", file=sys.stderr)
            print(line, file=sys.stderr)
            raise
        else:
            self.elements.append(elements.NumberedParagraph(num, line[indent:]))
            self._inelement = True

    def parseline(self, line, tocmatcher, forceindent=None):
        '''parseline(self, line, tocmatcher, forceindent=None): Parse a line.

        Parameters:
            - line: str, the line to parse
            - tocmatcher: toc.TOCMatcher, to identify titles and headings
            - forceindent: int, optional (default: the indent passed to
              __init__), the amount of indentation to expect for paragraphs'''
        indent = self._indent if forceindent is None else forceindent

        if not line:
            self._inelement = False
            return

        if indent == 0:
            self._parselinewithoutindent(line, tocmatcher)
        else:
            self._parselinewithindent(line, indent, tocmatcher)
