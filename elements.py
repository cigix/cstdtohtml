'''Package elements:

Contains definitions about the various structuring elements that make up a page.
'''

import sys

class Text:
    '''A text container.

    Attributes:
        - content: str, the text of the paragraph'''
    def __init__(self, content):
        self.content = content.strip()

    def addcontent(self, content):
        '''addcontent(self, content): Append to the contents.

        Parameters:
            - content: str, the text to append

        If the last word of the paragraph starts with "http://", the content
        gets concatenated directly. Otherwise, the content is concatenated with
        a newline character'''
        if self.content.split()[-1][:7] == "http://":
            self.content += content.strip()
        else:
            self.content += '\n' + content.strip()

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
        - lines: list of str, the lines of content'''
    def __init__(self, content):
        self.lines = list()
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
