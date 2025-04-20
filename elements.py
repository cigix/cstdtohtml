'''Package elements:

Contains definitions about the various structuring elements that make up a page.
'''

import re
import sys

# Line-breaks in hyperlinks can happen after the colon or the double slash.
HTTPBREAKRE = re.compile("https?:(//)?$")
# hyphenated phrases we don't want to dehyphenate when undoing line breaks
NOSTITCHING = (
    "60559-",          # ISO/IEC 60559-specified
    "bit-",            # bit-precise
    "const-",          # const-qualified
    "decimal-",        # decimal-point
    "derived-",        # derived-declarator-type-list
    "encoding-to-",    # encoding-to-encoding
    "end-of-",         # end-of-file
    "execution-",      # execution-time
    "floating-",       # floating-point
    "function-",       # function-like
    "half-",           # half-revolutions
    "implementation-", # implementation-defined
    "little-",         # little-endian
    "locale-",         # locale-specific
    "new-",            # new-line
    "non-",            # non-arithmetic, non-recursive, non-white-space
    "null-",           # null-terminated
    "pointer-to-",     # pointer-to-pointer
    "real-",           # real-floating
    "runtime-",        # runtime-constraints
    "single-",         # single-quotes
    "storage-",        # storage-class
    "string-from-",    # string-from-encoding
    "type-",           # type-generic
    "va-opt-"          # va-opt-replacement
)

class Text:
    '''A text container.

    Attributes:
        - content: str, the text of the paragraph
        - footnotes: set of int, the footnotes present in the content'''
    def __init__(self, content):
        self.content = content.strip()
        self.footnotes = set()

    def addcontent(self, content):
        '''addcontent(self, content): Append to the contents.

        Parameters:
            - content: str, the text to append

        If the current paragraph ends with a broken URL, the remainder of the
        hyperlink is concatenated with the current paragraph, then a newline,
        then the rest of content.
        If the current paragraph ends with a hyphen-broken word, the remainder
        of the word is stitched back with its beginning, then a newline, then
        the rest of content. "Stitching" involves removing the hyphen, except
        for the following hyphenated phrases:
            - ISO/IEC 60559-specified
            - bit-precise
            - const-qualified
            - decimal-point
            - derived-declarator-type-list
            - encoding-to-encoding
            - end-of-file
            - execution-time
            - floating-point
            - function-like
            - half-revolutions
            - implementation-defined
            - little-endian
            - locale-specific
            - new-line
            - non-arithmetic
            - non-recursive
            - non-white-space
            - null-terminated
            - pointer-to-pointer
            - real-floating
            - runtime-constraints
            - single-quotes
            - storage-class
            - string-from-encoding
            - type-generic
            - va-opt-replacement
        Otherwise, content is concatenated with a a newline.
        '''
        if not self.content:
            self.content = content.strip()
            return

        # "newline": concatenate '\n' + content
        # "first-word": concatenate first word of content + '\n' + rest of
        #               content
        # "dehyphenate": like "first word", but remove a hyphen from
        #                self.content first
        concatenation = "newline"
        if HTTPBREAKRE.search(self.content):
            concatenation = "first-word"
        elif self.content[-1] == '-':
            last_word = self.content.split()[-1]
            if last_word.lower() in NOSTITCHING:
                concatenation = "first-word"
            else:
                concatenation = "dehyphenate"

        if concatenation == "newline":
            self.content += '\n' + content.strip()
        if concatenation == "dehyphenate":
            self.content = self.content[:-1]
            concatenation = "first-word"
        if concatenation == "first-word":
            content_list = content.split(maxsplit=1)
            if len(content_list) == 1:
                # Only one word of content -> just concatenate
                self.content += content.strip()
            else:
                first_word, rest = content_list
                self.content += first_word.strip() + '\n' + rest.strip()

    def __str__(self):
        return self.content.replace('\n', r"\n")

class Paragraph(Text):
    '''Attributes:
        - content: str, see Text'''
    pass

class NumberedParagraph(Paragraph):
    '''Attributes:
        - number: int, the number associated to the paragraph
        - content: str, see Text'''
    def __init__(self, number, content):
        self.number = number
        Paragraph.__init__(self, content)

class NoteParagraph(NumberedParagraph):
    '''Attributes:
        - number: int, see NumberedParagraph
        - content: str, see Text'''
    def __str__(self):
        return "NOTE " + super().__str__()
class NoteNumberParagraph(NoteParagraph):
    '''Attributes:
        - notenumber: int, the number associated to the note
        - number: int, see NumberedParagraph
        - content: str, see Text'''
    def __init__(self, number, notenumber, content):
        self.notenumber = notenumber
        NoteParagraph.__init__(self, number, content)
    def __str__(self):
        return f"NOTE {self.notenumber} " + super().__str__()
class NoteToEntryParagraph(NoteNumberParagraph):
    def __str__(self):
        return f"Note {self.notenumber} to entry: " + super().__str__()

class ExampleParagraph(NumberedParagraph):
    '''Attributes:
        - number: int, see NumberedParagraph
        - content: str, see Text'''
    def __str__(self):
        return "EXAMPLE " + super().__str__()
class ExampleNumberParagraph(ExampleParagraph):
    '''Attributes:
        - examplenumber: int, the number associated to the example
        - number: int, see NumberedParagraph
        - content: str, see Text'''
    def __init__(self, number, examplenumber, content):
        self.examplenumber = examplenumber
        ExampleParagraph.__init__(self, number, content)
    def __str__(self):
        return f"EXAMPLE {self.examplenumber} " + super().__str__()

class UnorderedListItem(Text):
    '''A member of an unordered list.

    Attributes:
        - level: int, 1 if the bullet is '—', 2 if the bullet is '•'
        - indent: int, the number of spaces to expect at the beginning of
          similar items
        - see Text'''
    def __init__(self, line):
        try:
            (bullet, content) = line.split(maxsplit=1)
        except ValueError:
            print("Could not split bullet", file=sys.stderr)
            print(line, file=sys.stderr)
            raise
        else:
            if bullet == '—':
                self.level = 1
            elif bullet == '•':
                self.level = 2
            else:
                print("Unknown bullet:", bullet, file=sys.stderr)
                print(line, file=sys.stderr)
                raise NotImplementedError
            self.indent = len(line) - len(line.lstrip())
            Text.__init__(self, content)

    def __repr__(self):
        return "  " * (self.level - 1) + self.content

class OrderedListItem(Text):
    '''A member of an ordered list.

    Attributes:
        - number: int, the number of the item
        - see Text'''
    def __init__(self, line):
        try:
            (number, content) = line.split(maxsplit=1)
        except ValueError:
            print("Could not split line", file=sys.stderr)
            print(line, file=sys.stderr)
            raise
        else:
            try:
                self.number = int(number[:-1])
            except ValueError:
                print("Could not parse ordered item", file=sys.stderr)
                print(line, file=sys.stderr)
                raise
            else:
                Text.__init__(self, content)

class TitleHeading:
    '''A single standing title.

    Attributes:
        - content: str, the text of the heading'''
    def __init__(self, content):
        self.content = content.strip()

    def __repr__(self):
        return self.content

class NumberedHeading:
    '''A subsection heading, numbered, without a title.

    Attributes:
        - key: str, the key of the subsection'''
    def __init__(self, key):
        self.key = key.strip()

    def __repr__(self):
        return self.key

class NumberedTitleHeading(NumberedHeading, TitleHeading):
    '''Attributes:
        - see NumberedHeading
        - see TitleHeading'''
    def __init__(self, line):
        key, title = line.split(maxsplit=1)
        NumberedHeading.__init__(self, key)
        TitleHeading.__init__(self, title)

    def __repr__(self):
        return (NumberedHeading.__repr__(self)
                + ' '
                + TitleHeading.__repr__(self))

class Code:
    '''A text container. The contents are not left-stripped.

    Attributes:
        - lines: list of str, the lines of content
        - footnotes: set of int, the footnotes present in the content'''
    def __init__(self, content):
        self.lines = list()
        self.footnotes = set()
        self.addcontent(content)

    def addcontent(self, content):
        '''addcontent(self, content): Append to the contents.

        Parameters:
            - content: str, the text to append'''
        self.lines.append(content.rstrip())

    def __repr__(self):
        return repr(self.lines)

class NumberedCode(Code):
    '''Attributes:
        - number: int, the number associated to the code block
        - lines: list of str, see Code'''
    def __init__(self, number, content):
        self.number = number
        Code.__init__(self, content)

class ValueDefinition(Text):
    '''A value associated with a definition.

    Attributes:
        - value: str, the value being defined
        - see Text'''
    def __init__(self, value, content):
        value = value.strip()
        self.value = value[:-1] if value[-1] == ':' else value
        Text.__init__(self, content)

    def __str__(self):
        return self.value + ":\t" + Text.__str__(self)

class NumberedValueDefinition(ValueDefinition):
    '''Attributes:
        - number: int, the number associated to the definition
        - see ValueDefinition'''
    def __init__(self, number, value, content):
        self.number = number
        ValueDefinition.__init__(self, value, content)
