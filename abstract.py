'''Package abstract

Defines the structure storing the abstract pages.'''

import elements

class Abstract:
    '''A piece of content preceded by a title and a note.

    Attributes:
        - titleline: str, the title line
        - noteline: str, the centered note after the title
        - elements: list of elements.Paragraph, the contents of the abstract'''
    def __init__(self, abstractpages):
        '''Parameters:
            - abstractpages: list of page.Page, the Abstract pages'''
        contents = sum(map((lambda p: p.content), abstractpages), start=[])
        self.titleline = contents[0]
        self.noteline = contents[1]
        self.elements = list()
        for line in contents[2:]:
            if line[:8].isspace():
                self.elements.append(elements.Paragraph(line))
            else:
                self.elements[-1].addcontent(line)
