'''Package parser:

Defines LineParser, an object that turns lines into elements.'''

import re
import sys

import elements
import toc
import utils

# Paragraphs that end a "Syntax" section
AFTERSYNTAX = (
    "Constraints",
    "Description",
    "Semantics"
)
NOTINSYNTAX=0
STARTSYNTAX=1
STARTEDSYNTAX=2
# First word of first lines of Table F.2 in N3220 F.3p1
N3220_F3P1STARTS = (
    "setPayload",
    "convertFromHexCharacter",
    "restoreModes"
)

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
        # Are we in a "Syntax" section?
        self._insyntax = NOTINSYNTAX
        # Fix N3220 F.3p1: Long table with references
        self._inN3220_F3p1 = False

    def _parselinewithoutindent(self, line, tocmatcher):
        splits = line.split(maxsplit=1)
        groups = utils.groupwords(line)
        previous = self.elements[-1] if self.elements else None
        # Fix N3220 F.3p1: Long table with references
        if ("Table F.2: Operation binding" in line
            or splits[0] in N3220_F3P1STARTS):
            self._inN3220_F3p1 = True

        if line.lstrip()[:20] == "Forward references: ":
            # make it its own paragraph
            self.elements.append(elements.Paragraph(line))
            self._inelement = True
            return
        if line[:8] == "o,u,x,X ":
            # manual fix
            self.elements.append(elements.ValueDefinition(*splits))
            self._inelement = True
            return
        if tocmatcher.matchtitle(line):
            if (re.match(toc.KEYREGEX, splits[0])
                    or re.match(fr"{toc.CHAPTERREGEX}\.", splits[0])):
                # numbered title
                self.elements.append(elements.NumberedTitleHeading(line))
            else:
                # title
                self.elements.append(elements.TitleHeading(line))
            self._inelement = False
            return
        if tocmatcher.matchheading(line) and not self._inN3220_F3p1:
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
        #print(splits)
        if splits[0][:-1].isdigit() and splits[0][-1] == '.':
            # ordered list
            self.elements.append(elements.OrderedListItem(line))
            self._inelement = True
            return
        if len(splits) == 2:
            if line[3].isspace():
                # maybe value definition with number as value
                if utils.isint(line[:3]):
                    # value definition of number
                    self.elements.append(elements.ValueDefinition(*splits))
                    self._inelement = True
                    return
                if line[0] == '−' and utils.isint(line[1:3]):
                    # value definition of number, but with a misunderstood −
                    # U+2212 MINUS SIGN instead of a - U+002D HYPHEN-MINUS
                    self.elements.append(
                        elements.ValueDefinition(splits[0].replace('−', '-'),
                                                 splits[1]))
                    self._inelement = True
                    return
            if splits[0][:2] == "__" and splits[0][-2:] == "__":
                # value definition of preprocessing macro
                self.elements.append(elements.ValueDefinition(*splits))
                self._inelement = True
                return
            if line[0] == '%' and 2 <= len(splits[0]):
                # value definition of a format specifier
                self.elements.append(elements.ValueDefinition(*splits))
                self._inelement = True
                return

            if (not line[:2].isspace() # no or little indent
                    and len(groups) == 2): # only 2 groups
                stripped = line.lstrip() # remove any indentation
                l = len(groups[0])
                # if the second group starts between the 12th or 15th column,
                # and there are at least 4 spaces between groups
                if (12 <= stripped.find(groups[1], l) <= 15
                        and stripped[l:l + 4].isspace()):
                    # value definition of anything
                    self.elements.append(elements.ValueDefinition(*groups))
                    self._inelement = True
                    return

        if line[:4].isspace():
            # indented text?
            if self._inelement:
                # maybe it's part of the previous element ?
                def maybepreviouselement(previouselement, line):
                    if isinstance(previouselement, elements.Code):
                        return True
                    if isinstance(previouselement, elements.ValueDefinition):
                        return True
                    if isinstance(previouselement, elements.OrderedListItem):
                        return True
                    if isinstance(previouselement, elements.UnorderedListItem):
                        indent = previouselement.indent + 2
                        if (line[:indent].isspace()
                                and not line[indent].isspace()):
                            return True
                    return False
                if maybepreviouselement(previous, line):
                    previous.addcontent(line)
                    return
            if (self.elements
                    and isinstance(previous, elements.UnorderedListItem)
                    and previous.level > 1):
                # indented paragraph, inside a list
                self.elements.append(elements.Paragraph(line))
                self._inelement = True
                return
            if line[:7].isspace():
                # code block
                # If the previous element is also Code, then this is the same
                # element with an empty line which made _inelement == False
                if isinstance(previous, elements.Code):
                    previous.lines.append("")
                    previous.lines.append(line)
                else:
                    self.elements.append(elements.Code(line))
                self._inelement = True
                return
            # idk, make it a paragraph

        # Fix N3220 6.4.4.2p8: Code block with no indent
        # Fix N3220 F.3p1: Long table with references
        if ("/* Yields a" in line
            or self._inN3220_F3p1):
            if isinstance(previous, elements.Code):
                previous.lines.append(line)
            else:
                self.elements.append(elements.Code(line))
            self._inelement = True
            return

        # regular text
        if (self._inelement
                and isinstance(previous, elements.Text)
                and not isinstance(previous, elements.ValueDefinition)):
            # continuation of previous text element
            previous.addcontent(line)
            return

        # new paragraph
        if self._insyntax != NOTINSYNTAX and line in AFTERSYNTAX:
            self._insyntax = NOTINSYNTAX

        if self._insyntax != NOTINSYNTAX:
            self.elements.append(elements.Code(line))
            self._insyntax = STARTEDSYNTAX
        else:
            self.elements.append(elements.Paragraph(line))
            if line == "Syntax":
                self._insyntax = STARTSYNTAX
        self._inelement = True
        return

    def _parselinewithindent(self, line, indent, tocmatcher):
        if line[:indent].isspace():
            #print(f"{indent}\t|{line[indent:]}")
            self._parselinewithoutindent(line[indent:], tocmatcher)
            return
        try:
            num = int(line[:indent])
        except:
            print(f"Could not parse indent of {indent}", file=sys.stderr)
            print(line, file=sys.stderr)
            raise
        else:
            unindented = line[indent:]
            if unindented[:7].isspace() or self._insyntax == STARTSYNTAX:
                self.elements.append(elements.NumberedCode(num, unindented))
            else:
                # NumberedParagraph
                self._insyntax = NOTINSYNTAX
                self._inN3220_F3p1 = False
                splits = unindented.split(maxsplit=2)
                firstword = splits[0] if splits else ""
                secondisint = 2 <= len(splits) and utils.isint(splits[1])
                if firstword == "NOTE":
                    if secondisint:
                        newelem = elements.NoteNumberParagraph(
                                num, int(splits[1]), " ".join(splits[2:]))
                    else:
                        newelem = elements.NoteParagraph(
                                num, " ".join(splits[1:]))
                elif (firstword == "Note" and secondisint
                      and splits[2].startswith("to entry: ")):
                    newelem = elements.NoteToEntryParagraph(
                            num, int(splits[1]), splits[2][10:])
                elif firstword == "EXAMPLE":
                    if secondisint:
                        newelem = elements.ExampleNumberParagraph(
                                num, int(splits[1]), " ".join(splits[2:]))
                    else:
                        newelem = elements.ExampleParagraph(
                                num, " ".join(splits[1:]))
                else:
                    newelem = elements.NumberedParagraph(num, unindented)
                self.elements.append(newelem)

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
