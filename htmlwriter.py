'''Package htmlwriter:

This package implements objects that eat pages.StructuredPages and turns them
into HTML.'''

import html
import re
import sys

import elements
import pages

def htmlformat(string, newlines=True):
    '''format(string): Replace placeholders and special characters.

    Parameters:
        - string: str, the string to format
        - newlines: bool, optional (default: True), should newlines be augmented
          with <br>
    '''
    string = string.replace('\x03', '□')
    string = string.replace('\x06', '')
    string = string.replace('\x07', '')
    string = html.escape(string)
    if newlines:
        string = string.replace('\n', "<br>\n")
    string = re.sub("\x1bfootnote(.*?)\x1b",
                    r'<a href="#footnote\g<1>" class="footnote">\g<1>)</a>',
                    string)
    string = re.sub("\x1blinkhttp(.*?)\x1b",
                    r'<a href="http\g<1>">http\g<1></a>', string)
    string = re.sub("\x1blink(.*?)\x1b", r'<a href="#\g<1>">\g<1></a>', string)
    return string

class Tag:
    '''Attributes:
        - depth: int, the depth in the DOM
        - tag: str, the type of tag
        - attributes: str or None, the attributes on the tag
        - contents: str or Tag or list of str or Tag, the contents of the tag'''
    def __init__(self, depth, tag, contents):
        '''tag is split into self.tag and self.attributes'''
        self.depth = depth
        split = tag.split(maxsplit=1)
        if len(split) == 2:
            self.tag = split[0]
            self.attributes = split[1]
        else:
            self.tag = tag
            self.attributes = None
        self.contents = list()
        if type(contents) is list:
            for content in contents:
                self.add(content)
        else:
            self.add(contents)

    def add(self, content):
        '''add(self, content): Add to the tags contents.

        Parameters:
            - content: str or Tag, the content to add'''
        if type(content) is str:
            self.contents += content.splitlines()
        elif isinstance(content, Tag):
            self.contents.append(content)
        else:
            raise ValueError(
                f"Wrong content type: {content.__class__.__name__}")

    def __repr__(self):
        res = self.tag
        if self.attributes is not None:
            res += " " + self.attributes
        if self.contents:
            res += ':'
            for c in self.contents:
                r = repr(c)
                for line in r.splitlines():
                    res += "\n  " + line
        return res

    def tohtml(self):
        res = '<' + self.tag
        if self.attributes is not None:
            res += ' ' + self.attributes
        res += ">\n"
        for content in self.contents:
            if isinstance(content, Tag):
                string = content.tohtml()
            else:
                string = content
            for line in string.splitlines():
                res += "  " + line + '\n'
        res += "</" + self.tag + ">\n"
        return res

class DOMEater:
    '''Attributes:
        - key: str, the last key seen
        - body: Tag, the root tag'''
    def __init__(self):
        self.key = None
        self.body = Tag(-1, "body", list())

    def eat(self, page):
        '''eat(self, page): Eat a StructuredPage.

        Read all the elements of the page and turn them into HTML tags.'''
        tagstack = list()
        if isinstance(page, pages.CoverPage):
            self.body.add(Tag(0, "h1", page.title))

        for i, elem in enumerate(page.elements):
            if type(elem) is elements.Paragraph:
                # If:
                #   paragraph is sandwidched between unorderedlistitems
                #   and the previous is deeper that the next
                if (tagstack
                        and i < len(page.elements) - 1
                        and tagstack[-1].tag == "li"
                        and (type(page.elements[i - 1])
                             == type(page.elements[i + 1])
                             == elements.UnorderedListItem)
                        and (page.elements[i - 1].level
                             > page.elements[i + 1].level)):
                    # Paragraph belongs to the parent li of the previous li
                    tagstack.pop() # pop li, top is ul
                    tagstack.pop() # pop ul, top is li
                    p = Tag(len(tagstack), "p", htmlformat(elem.content))
                    tagstack[-1].contents.append(p)
                    tagstack.append(p)
                    continue
                p = Tag(0, "p", htmlformat(elem.content))
                tagstack = [p]
                self.body.add(p)
                continue
            if type(elem) is elements.NumberedParagraph:
                parkey = f"{self.key}.p{elem.number}"
                p = Tag(0, f'p id="{parkey}"', list())
                aside = Tag(1, "aside", f'<a href="#{parkey}">{elem.number}</a>')
                p.contents.append(aside)
                p.contents.append(htmlformat(elem.content))
                tagstack = [p]
                self.body.add(p)
                continue
            if type(elem) is elements.UnorderedListItem:
                depthli = elem.level * 2 - 1
                depthul = depthli - 1
                # 3 cases:
                #   - unordered list already exists at this level, add to it
                #   - unordered list exists at the previous level, create nested
                #     list
                #   - create unordered list at root level
                if len(tagstack) > depthul and tagstack[depthul].tag == "ul":
                    # unordered list already exists at this level, add to it
                    li = Tag(depthli, "li", htmlformat(elem.content))
                    tagstack[depthul].add(li)
                    # pop everything at depthli and above, push li
                    tagstack[depthli:] = [li]
                    continue
                if (depthul - 2 >= 0
                        and len(tagstack) > depthul - 1
                        and tagstack[depthul - 2].tag == "ul"
                        and tagstack[depthul - 1].tag == "li"):
                    # unordered list exists at the previous level, create nested
                    # list
                    li = Tag(depthli, "li", htmlformat(elem.content))
                    ul = Tag(depthul, "ul", li)
                    tagstack[depthul - 1].add(ul)
                    # pop everything at depthul and above, push ul, push li
                    tagstack[depthul:] = [ul, li]
                    continue
                if depthul == 0:
                    # create unordered list at root level
                    li = Tag(1, "li", htmlformat(elem.content))
                    ul = Tag(0, "ul", li)
                    tagstack = [ul, li]
                    self.body.add(ul)
                    continue
                print("Invalid UnorderedListItem depth:", elem.level,
                      file=sys.stderr)
                print(elem, file=sys.stderr)
                print("tagstack:", [t.tag for t in tagstack], file=sys.stderr)
                print(repr(self.body.contents[-1]), file=sys.stderr)
                raise RuntimeError
            if type(elem) is elements.OrderedListItem:
                if len(tagstack) >= 2 and tagstack[0].tag == 'ol':
                    if tagstack[1].number + 1 != elem.number:
                        print("Non-consecutive OrderedListItems:",
                              tagstack[1].number, "and", elem.number,
                              file=sys.stderr)
                        print(elem, file=sys.stderr)
                        print(repr(self.body), file=sys.stderr)
                        print("tagstack:", [t.tag for t in tagstack],
                              file=sys.stderr)
                        raise RuntimeError
                    tagstack[1:] = [] # pop everything above ol, top is ol
                    li = Tag(1, "li", htmlformat(elem.content))
                    li.number = elem.number
                    tagstack[0].add(li)
                    tagstack.append(li)
                    continue
                if elem.number != 1:
                    print("Ordered list starting at", elem.number,
                          file=sys.stderr)
                    print(elem, file=sys.stderr)
                    raise RuntimeError
                li = Tag(1, "li", elem.content)
                li.number = 1
                ol = Tag(0, "ol", li)
                tagstack = [ol, li]
                self.body.add(ol)
                continue
            if type(elem) is elements.TitleHeading:
                if elem.content[:6] == "Annex ":
                    key = elem.content[6:]
                else:
                    key = elem.content
                h1 = Tag(0, f'h1 id="{key}"',
                         f'<a href="#{key}">{elem.content}</a>')
                tagstack = list()
                self.body.add(h1)
                self.key = key
                continue
            if type(elem) is elements.NumberedHeading:
                level = elem.key.count('.') + 1
                h = Tag(0, f'h{level} id="{elem.key}"',
                        f'<a href="#{elem.key}">{elem.key}</a>')
                tagstack = list()
                self.body.add(h)
                self.key = elem.key
                continue
            if type(elem) is elements.NumberedTitleHeading:
                key = elem.key
                if key[-1] == '.':
                    key = key[:-1]
                level = key.count('.') + 1
                h = Tag(0, f'h{level} id="{key}"',
                        f'<a href="#{key}">{elem.key} '
                        f'{htmlformat(elem.content)}</a>')
                tagstack = list()
                self.body.add(h)
                self.key = key
                continue
            if type(elem) is elements.Code:
                lines = [htmlformat(l, False) for l in elem.lines]
                if tagstack and tagstack[-1].tag == 'li':
                    pre = Tag(len(tagstack), "pre", lines)
                    tagstack[-1].add(pre)
                    continue
                pre = Tag(0, "pre", lines)
                tagstack = list()
                self.body.add(pre)
                continue
            if type(elem) is elements.NumberedCode:
                parkey = f"{self.key}.p{elem.number}"
                aside = Tag(1, "aside",
                            f'<a href="#{parkey}">{elem.number}</a>')
                lines = [htmlformat(l, False) for l in elem.lines]
                pre = Tag(1, f'pre id="#{parkey}"', lines)
                div = Tag(0, "div", aside)
                div.add(pre)
                tagstack = list()
                self.body.add(div)
                continue
            if type(elem) is elements.ValueDefinition:
                dt = Tag(1, "dt", htmlformat(elem.value))
                dd = Tag(1, "dd", htmlformat(elem.content))
                if len(tagstack) >= 1 and tagstack[0].tag == "dl":
                    tagstack[0].add(dt)
                    tagstack[0].add(dd)
                    continue
                dl = Tag(0, "dl", dt)
                dl.add(dd)
                tagstack = [dl]
                self.body.add(dl)
                continue

            raise ValueError(
                f"Unknown type of element: {elem.__class__.__name__}")

    def eatabstract(self, abstract):
        '''eatabstract(self, abstract): Eat an Abstract.

        Read all the elements of the page and turn them into HTML tags.'''
        title = htmlformat(abstract.titleline.strip())
        self.body.add(Tag(0, f'h1 id="{title}"',
                          f'<a href="#{title}">{title}</a>'))
        self.body.add(Tag(0, "p", htmlformat(abstract.noteline.strip())))
        for elem in abstract.elements:
            self.body.add(Tag(0, "p", htmlformat(elem.content)))

    def eattoc(self, toc):
        '''eattoc(self, toc): Eat a TOC.

        Turn a toc.TOC into HTML tags.'''
        title = htmlformat(toc.titleline.strip())
        self.body.add(Tag(0, f'h1 id="{title}"',
                          f'<a href="#{title}">{title}</a>'))
        main = Tag(0, "ul", list())
        self.body.add(main)
        # list of tuple (str, Tag), the hierachical stack of ul Tags. A key with
        # n dots is a child of levels[n][1]
        levels = [(None, main)]
        lastli = None
        for title, key in toc.titles:
            if key is None:
                if title[:6] == "Annex ":
                    key = title[6]
                    li = Tag(1, "li", f'<a href="#{key}">{title}</a>')
                    lastli = li
                else:
                    li = Tag(1, "li", f'<a href="#{title}">{title}</a>')
                    lastli = None
                main.add(li)
                levels[1:] = []
            else:
                level = key.count('.')
                li = Tag(level * 2 - 1, "li",
                         f'{key} <a href="#{key}">{htmlformat(title)}</a>')
                if level == len(levels):
                    # one deeper than the last
                    ul = Tag(level * 2 - 2, "ul", li)
                    lastli.add(ul)
                    lastkey = lastli.contents[0].split(maxsplit=1)[0]
                    levels.append((lastkey, ul))
                    lastli = li
                elif level < len(levels):
                    # same level or higher that last
                    levels[level + 1:] = []
                    levels[level][1].add(li)
                    lastli = li
                else:
                    print("Invalid TOC hierarchy", file=sys.stderr)
                    print("Entry:", key, title, file=sys.stderr)
                    print("Levels len:", len(levels), file=sys.stderr)
                    raise ValueError

    def tohtml(self):
        return self.body.tohtml()
