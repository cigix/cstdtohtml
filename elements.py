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
        gets concatenated directly. If the paragraph ended with a dash ('-'), it
        is removed and the content gets concatenated directly. In any other
        case, a space is introduced during the concatenation.'''
        if self.content.split()[-1][:7] == "http://":
            self.content += content.strip()
        elif self.content[-1] == '-':
            self.content = self.content[:-1] + content.strip()
        else:
            self.content += ' ' + content.strip()

class Paragraph(Text):
    '''Attributes:
        - content: str, see Text'''
    pass

class NumberedParagraph(Text):
    '''Attributes:
        - number: int, the number associated to the paragraph
        - content: str, see Text'''
    def __init__(self, content):
        try:
            (number, text) = content.split(maxsplit=1)
        except ValueError:
            print("Could not split number", file=sys.stderr)
            print(content, file=sys.stderr)
            raise
        else:
            try:
                self.number = int(number)
            except ValueError:
                print("Could not parse numbered paragraph", file=sys.stderr)
                print(content, file=sys.stderr)
            Text.__init__(self, text)

class UnorderedListItem(Text):
    '''A member of an unordered list.

    Attributes:
        - level: int, 1 if the bullet is '—', 2 if the bullet is '•'
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
            Text.__init__(self, content)

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

class Heading:
    '''Attributes:
        - level: int, the depth of the heading, default: 6
        - content: str, the text of the heading'''
    def __init__(self, level, content):
        self.level = level
        self.content = content.strip()

    @staticmethod
    def fromnumberedtitle(title):
        '''fromnumberedtitle(title): Create a Heading with correct level
        according to section numbering.

        Return: Heading'''
        split = title.split(maxsplit=1)
        level = split[0].count('.') + 1
        return Heading(level, title)
