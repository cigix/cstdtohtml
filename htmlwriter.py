'''Package htmlwriter:

This package implements objects that eat pages.StructuredPages and turns them
into HTML.'''

import html
import re
import sys

import elements
import pages
import toc

def htmlformat(string, newlines=True):
    '''htmlformat(string): Replace placeholders and special characters.

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
    string = re.sub(f"(annex\\s)\x1blink({toc.ANNEXREGEX})\x1b",
                    r'<a href="#\g<2>">\g<1>\g<2></a>', string)
    string = re.sub(f"(clause\\s)\x1blink({toc.CHAPTERREGEX})\x1b",
                    r'<a href="#\g<2>">\g<1>\g<2></a>', string)
    string = re.sub("\x1blink(.*?)\x1b", r'<a href="#\g<1>">\g<1></a>', string)
    return string

class Tag:
    '''Attributes:
        - tag: str, the type of tag
        - attributes: str or None, the attributes on the tag
        - contents: str or Tag or list of str or Tag, the contents of the tag'''
    def __init__(self, tag, contents=None):
        '''tag is split into self.tag and self.attributes'''
        split = tag.split(maxsplit=1)
        if len(split) == 2:
            self.tag = split[0]
            self.attributes = split[1]
        else:
            self.tag = tag
            self.attributes = None
        self.contents = list()
        if contents is not None:
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
        '''tohtml(self): Turn the Tag into an HTML string'''
        res = '<' + self.tag
        if self.attributes is not None:
            res += ' ' + self.attributes
        res += ">\n"
        if self.attributes and self.attributes[-1] == '/':
            # self closing, no-content tag
            return res
        for content in self.contents:
            if isinstance(content, Tag):
                string = content.tohtml()
            else:
                string = content
            for line in string.splitlines():
                res += "  " + line + '\n'
        res += "</" + self.tag + ">\n"
        return res

def footnotetohtml(footnoteid, elems):
    '''footnotetohtml(footnoteid, elems): Turn a footnote into a HTML tag.

    Return a Tag.'''
    aside = Tag("aside", f'<a href="#footnote{footnoteid}">{footnoteid})</a>')
    div = Tag(f'div id="footnote{footnoteid}"', aside)
    for elem in elems:
        if type(elem) is elements.Paragraph:
            div.add(Tag("p", htmlformat(elem.content)))
        elif type(elem) is elements.Code:
            lines = [htmlformat(l, False) for l in elem.lines]
            div.add(Tag("pre", lines))
        else:
            raise ValueError(
                f"Unknown type in footnotes: {elem.__class__.__name__}")
    return div

def eatfootnotes(root, footnotes):
    '''eatfootnotes(root, footnotes): Eat footnotes.

    Turn a footnote dict into HTML tags.'''
    for footnote in sorted(footnotes.keys()):
        root.add(footnotetohtml(footnote, footnotes[footnote]))

def eatStructuredPage(root, page):
    '''eatStructuredPage(page, root): Eat a StructuredPage.

    Parameters:
        - root: Tag, the tag to which generated tags will be added
        - page: StructuredPage, the page to turn to HTML tags

    Read all the elements of the page and turn them into HTML tags.'''
    tagstack = list()
    key = None # the last key seen
    if isinstance(page, pages.CoverPage):
        root.add(Tag("h1", page.title))

    dumpedfootnotes = set()
    todumpfootnotes = set()
    def dumpfootnotes():
        nonlocal tagstack, dumpedfootnotes, todumpfootnotes
        for footnote in sorted(todumpfootnotes):
            root.add(footnotetohtml(footnote, page.footnotes[footnote]))
        tagstack = []
        dumpedfootnotes.update(todumpfootnotes)
        todumpfootnotes = set()

    for i, elem in enumerate(page.elements):
        if isinstance(elem, elements.Text):
            todumpfootnotes.update(elem.footnotes)
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
                p = Tag("p", htmlformat(elem.content))
                tagstack[-1].contents.append(p)
                tagstack.append(p)
                continue
            p = Tag("p", htmlformat(elem.content))
            tagstack = [p]
            root.add(p)
            continue
        if type(elem) is elements.NumberedParagraph:
            parkey = f"{key}.p{elem.number}"
            p = Tag(f'p id="{parkey}"')
            aside = Tag("aside", f'<a href="#{parkey}">{elem.number}</a>')
            p.contents.append(aside)
            p.contents.append(htmlformat(elem.content))
            tagstack = [p]
            root.add(p)
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
                li = Tag("li", htmlformat(elem.content))
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
                li = Tag("li", htmlformat(elem.content))
                ul = Tag("ul", li)
                tagstack[depthul - 1].add(ul)
                # pop everything at depthul and above, push ul, push li
                tagstack[depthul:] = [ul, li]
                continue
            if depthul == 0:
                # create unordered list at root level
                li = Tag("li", htmlformat(elem.content))
                ul = Tag("ul", li)
                tagstack = [ul, li]
                root.add(ul)
                continue
            print("Invalid UnorderedListItem depth:", elem.level,
                  file=sys.stderr)
            print(elem, file=sys.stderr)
            print("tagstack:", [t.tag for t in tagstack], file=sys.stderr)
            print(repr(root.contents[-1]), file=sys.stderr)
            raise RuntimeError
        if type(elem) is elements.OrderedListItem:
            if len(tagstack) >= 2 and tagstack[0].tag == 'ol':
                if tagstack[1].number + 1 != elem.number:
                    print("Non-consecutive OrderedListItems:",
                          tagstack[1].number, "and", elem.number,
                          file=sys.stderr)
                    print(elem, file=sys.stderr)
                    print(repr(root), file=sys.stderr)
                    print("tagstack:", [t.tag for t in tagstack],
                          file=sys.stderr)
                    raise RuntimeError
                tagstack[1:] = [] # pop everything above ol, top is ol
                li = Tag("li", htmlformat(elem.content))
                li.number = elem.number
                tagstack[0].add(li)
                tagstack.append(li)
                continue
            if elem.number != 1:
                print("Ordered list starting at", elem.number, file=sys.stderr)
                print(elem, file=sys.stderr)
                raise RuntimeError
            li = Tag("li", elem.content)
            li.number = 1
            ol = Tag("ol", li)
            tagstack = [ol, li]
            root.add(ol)
            continue
        if type(elem) is elements.TitleHeading:
            dumpfootnotes()
            if elem.content[:6] == "Annex ":
                key = elem.content[6:]
            else:
                key = elem.content
            h1 = Tag(f'h1 id="{key}"', f'<a href="#{key}">{elem.content}</a>')
            root.add(h1)
            continue
        if type(elem) is elements.NumberedHeading:
            dumpfootnotes()
            level = elem.key.count('.') + 1
            key = elem.key
            h = Tag(f'h{level} id="{key}"', f'<a href="#{key}">{key}</a>')
            root.add(h)
            continue
        if type(elem) is elements.NumberedTitleHeading:
            dumpfootnotes()
            key = elem.key
            if key[-1] == '.':
                key = key[:-1]
            level = key.count('.') + 1
            h = Tag(f'h{level} id="{key}"', f'<a href="#{key}">{elem.key} '
                    f'{htmlformat(elem.content)}</a>')
            root.add(h)
            continue
        if type(elem) is elements.Code:
            lines = [htmlformat(l, False) for l in elem.lines]
            if tagstack and tagstack[-1].tag == 'li':
                pre = Tag("pre", lines)
                tagstack[-1].add(pre)
                continue
            pre = Tag("pre", lines)
            tagstack = list()
            root.add(pre)
            continue
        if type(elem) is elements.NumberedCode:
            parkey = f"{key}.p{elem.number}"
            aside = Tag("aside", f'<a href="#{parkey}">{elem.number}</a>')
            lines = [htmlformat(l, False) for l in elem.lines]
            pre = Tag(f'pre id="#{parkey}"', lines)
            div = Tag("div", aside)
            div.add(pre)
            tagstack = list()
            root.add(div)
            continue
        if type(elem) is elements.ValueDefinition:
            dt = Tag("dt", htmlformat(elem.value))
            dd = Tag("dd", htmlformat(elem.content))
            if tagstack and tagstack[0].tag == "dl":
                tagstack[0].add(dt)
                tagstack[0].add(dd)
                continue
            dl = Tag("dl", dt)
            dl.add(dd)
            tagstack = [dl]
            root.add(dl)
            continue

        raise ValueError(
            f"Unknown type of element: {elem.__class__.__name__}")

    dumpfootnotes()
    return dumpedfootnotes

def eatAbstract(root, abstract):
    '''eatAbstract(root, abstract): Eat an Abstract.

    Read all the elements of the page and turn them into HTML tags.'''
    title = htmlformat(abstract.titleline.strip())
    root.add(Tag(f'h1 id="{title}"', f'<a href="#{title}">{title}</a>'))
    root.add(Tag("p", htmlformat(abstract.noteline.strip())))
    for elem in abstract.elements:
        root.add(Tag("p", htmlformat(elem.content)))

def eatTOC(root, t):
    '''eatTOC(root, t): Eat a TOC.

    Turn a toc.TOC into HTML tags.'''
    title = htmlformat(t.titleline.strip())
    root.add(Tag(f'h1 id="{title}"', f'<a href="#{title}">{title}</a>'))
    main = Tag("ul")
    root.add(main)
    # list of tuple (str, Tag), the hierachical stack of ul Tags. A key with
    # n dots is a child of levels[n][1]
    levels = [(None, main)]
    lastli = None
    for title, key in t.titles:
        if key is None:
            if title[:6] == "Annex ":
                key = title[6]
                li = Tag("li", f'<a href="#{key}">{title}</a>')
                lastli = li
            else:
                li = Tag("li", f'<a href="#{title}">{title}</a>')
                lastli = None
            main.add(li)
            levels[1:] = []
        else:
            level = key.count('.')
            li = Tag("li", f'{key} <a href="#{key}">{htmlformat(title)}</a>')
            if level == len(levels):
                # one deeper than the last
                ul = Tag("ul", li)
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
