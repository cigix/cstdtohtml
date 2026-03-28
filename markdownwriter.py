'''Package markdownwriter:

This package implements objects that eat pages.StructuredPages and turns them
into Pandoc flavoured Markdown.'''

import re
import sys

import elements
import pages
import toc

def mdformat(string, newlines=True):
    '''mdformat(string): Replace placeholders and special characters.

    Parameters:
        - string: str, the string to format
        - newlines: bool, optional (default: True), should newlines be escaped
    '''
    if newlines:
        string = string.replace('\n', "\\\n")
        string = string.replace('_', "\\_")
        string = string.replace('*', "\\*")
        # Lines starting with "(<number>)" are considered as ordered lists
        string = re.sub(r"^\(\d+\)", r"\\\g<0>", string)
    string = re.sub("\x1bfootnote(.*?)\x1b", r"[^\g<1>]", string)
    string = re.sub("\x1blinkhttp(.*?)\x1b", r"<http\g<1>>", string)
    string = re.sub(f"(annex\\s)\x1blink({toc.ANNEXREGEX})\x1b",
                    r'[\g<1>\g<2>](#\g<2>)', string)
    string = re.sub(f"(clause\\s)\x1blink({toc.CHAPTERREGEX})\x1b",
                    r'[\g<1>\g<2>](#\g<2>)', string)
    string = re.sub("\x1blink(.*?)\x1b", r'[\g<1>](#\g<1>)', string)
    return string

def indent(chunk, columns):
    '''indent(chunk, columns): Indent all non-empty lines in a chunk.'''
    i = " " * columns
    result = str()
    for line in chunk.splitlines():
        if line:
            result += i + line
        result += '\n'
    return result

def footnotetomd(footnoteid, elems):
    '''footnotetomd(footnoteid, elems): Turn a footnote into a Markdown chunk.
    '''
    subchunks = list()
    for elem in elems:
        subchunk = str()
        if type(elem) is elements.Paragraph:
            subchunk = mdformat(elem.content)
        elif type(elem) is elements.Code:
            subchunk = "```\n"
            for line in elem.lines:
                subchunk += mdformat(line, False)
            subchunk += "\n```"
        else:
            raise ValueError(
                f"Unknown type in footnotes: {elem.__class__.__name__}")
        subchunks.append(subchunk)
    footnotecontent = '\n'.join(subchunks)
    return f"[^{footnoteid}]:\n" + indent(footnotecontent, 4)

def eatfootnotes(footnotes):
    '''eatfootnotes(footnotes): Turn a footnote dict into Markdown.'''
    chunks = [
            footnotetomd(footnote, footnotes[footnote])
            for footnote in sorted(footnotes.keys())
        ]
    return '\n'.join(chunks)

def eatStructuredPage(page, donefootnotes):
    '''eatStructuredPage(page, donefootnotes): Eat a StructuredPage.

    Parameters:
        - page: StructuredPage, the page to turn to Markdown
        - donefootnotes: set of int, the set of footnotes that have already been
          dumped, and should not be dumped again

    Read all the elements of the page and turn them into Markdown.

    This function adds entries to donefootnotes.
    '''
    chunks = list()
    key = None # the last key seen
    if isinstance(page, pages.CoverPage):
        chunks.append(f"# {page.title}")

    todumpfootnotes = set()
    def dumpfootnotes():
        nonlocal donefootnotes, todumpfootnotes
        for footnote in sorted(todumpfootnotes - donefootnotes):
            chunks.append(footnotetomd(footnote, page.footnotes[footnote]))
        donefootnotes.update(todumpfootnotes)
        todumpfootnotes = set()

    nestinglevel = 0

    for i, elem in enumerate(page.elements):
        if isinstance(elem, elements.Text) or isinstance(elem, elements.Code):
            todumpfootnotes.update(elem.footnotes)
        if type(elem) is elements.Paragraph:
            # If:
            #   paragraph is sandwidched between unorderedlistitems
            #   and the previous is deeper that the next
            if (nestinglevel
                    and i < len(page.elements) - 1
                    and (type(page.elements[i - 1])
                         == type(page.elements[i + 1])
                         == elements.UnorderedListItem)
                    and (page.elements[i - 1].level
                         > page.elements[i + 1].level)):
                # Paragraph belongs to the parent list of the previous list
                nestinglevel -= 1
            else:
                nestinglevel = 0
            chunk = mdformat(elem.content)
            if nestinglevel:
                chunk = indent(chunk, nestinglevel * 4)
            chunks.append(chunk)
            continue
        if type(elem) is elements.NumberedParagraph:
            parkey = f"{key}.p{elem.number}"
            # link pointing to anchor, with id of the anchor
            chunk = f"[{elem.number}](#{parkey}){{#{parkey}}} "
            chunk += mdformat(elem.content)
            chunks.append(chunk)
            nestinglevel = 0
            continue
        if type(elem) in (elements.NoteParagraph, elements.NoteNumberParagraph,
                          elements.ExampleParagraph,
                          elements.ExampleNumberParagraph):
            if type(elem) is elements.NoteParagraph:
                start = "note"
                number = None
            if type(elem) is elements.NoteNumberParagraph:
                start = "note"
                number = elem.notenumber
            if type(elem) is elements.ExampleParagraph:
                start = "example"
                number = None
            if type(elem) is elements.ExampleNumberParagraph:
                start = "example"
                number = elem.examplenumber
            parkey = f"{key}.p{elem.number}"
            chunk = f"[{elem.number}](#{parkey}){{#{parkey}}} "
            startcontent = start.upper()
            if number is not None:
                startcontent += ' ' + str(number)
            chunk += startcontent + ' '
            if elem.content:
                chunk += mdformat(elem.content)
            chunks.append(chunk)
            nestinglevel = 0
            continue
        if type(elem) is elements.NoteToEntryParagraph:
            parkey = f"{key}.p{elem.number}"
            chunk = f"[{elem.number}](#{parkey}){{#{parkey}}} "
            chunk += f"Note {elem.notenumber} to entry:\n"
            chunk += mdformat(elem.content)
            chunks.append(chunk)
            nestinglevel = 0
            continue
        if type(elem) is elements.UnorderedListItem:
            chunk = "* " + mdformat(elem.content)
            chunk = indent(chunk, (elem.level - 1) * 4)
            if nestinglevel == 0:
                chunks.append(chunk)
            else:
                chunks[-1] += chunk
            nestinglevel = elem.level
            continue
        if type(elem) is elements.OrderedListItem:
            # ordered lists seem to only exist at root level
            chunk = f"{elem.number}. " + mdformat(elem.content)
            if nestinglevel == 0:
                chunks.append(chunk)
            else:
                chunks[-1] += chunk
            nestinglevel = 0
            continue
        if type(elem) is elements.TitleHeading:
            dumpfootnotes()
            if elem.content[:6] == "Annex ":
                key = elem.content[6:]
            else:
                key = elem.content
            chunk = f"# [{elem.content}](#{key}) {{#{key}}}"
            chunks.append(chunk)
            nestinglevel = 0
            continue
        if type(elem) is elements.NumberedHeading:
            dumpfootnotes()
            level = elem.key.count('.') + 1
            key = elem.key
            chunk = '#' * level + f" [{key}](#{key}) {{#{key}}}"
            chunks.append(chunk)
            nestinglevel = 0
            continue
        if type(elem) is elements.NumberedTitleHeading:
            dumpfootnotes()
            key = elem.key
            if key[-1] == '.':
                key = key[:-1]
            level = key.count('.') + 1
            chunk = '#' * level
            chunk += f" [{elem.key} {mdformat(elem.content)}](#{key})"
            chunk += " {#" + key + "}\n"
            chunks.append(chunk)
            nestinglevel = 0
            continue
        if type(elem) is elements.Code:
            lines = [mdformat(l, False) for l in elem.lines]
            chunk = "```\n" + '\n'.join(lines) + "\n```"
            if nestinglevel:
                chunk = indent(chunk, nestinglevel * 4)
            chunks.append(chunk)
            continue
        if type(elem) is elements.NumberedCode:
            parkey = f"{key}.p{elem.number}"
            lines = [mdformat(l, False) for l in elem.lines]
            # link pointing to anchor, with id of the anchor
            chunk = f"[{elem.number}](#{parkey})\n"
            chunk += f"``` {{#{parkey}}}\n" + '\n'.join(lines) + "\n```"
            if nestinglevel:
                chunk = indent(chunk, nestinglevel * 4)
            chunks.append(chunk)
            continue
        if type(elem) is elements.ValueDefinition:
            chunk = mdformat(elem.value) + "\n"
            chunk += ": " + mdformat(elem.content)
            if nestinglevel:
                chunk = indent(chunk, nestinglevel * 4)
            chunks.append(chunk)
            continue

        raise ValueError(
            f"Unknown type of element: {elem.__class__.__name__}")

    dumpfootnotes()
    return "\n\n".join(chunks)

def eatAbstract(abstract):
    '''eatAbstract(abstract): Eat an Abstract.

    Read all the elements of the page and turn them into Markdown.'''
    chunks = list()
    title = mdformat(abstract.titleline.strip())
    chunks.append(f"# [{title}](#{title}) {{#{title}}}")
    chunks.append(mdformat(abstract.noteline.strip()))
    for elem in abstract.elements:
        chunks.append(mdformat(elem.content))
    return "\n\n".join(chunks)

def eatTOC(t):
    '''eatTOC(t): Eat a TOC.

    Turn a toc.TOC into Markdown.'''
    title = mdformat(t.titleline.strip())
    titlechunk = f"# [{title}](#{title}) {{#{title}}}"
    nestinglevel = 0
    listchunk = str()
    for title, key in t.titles:
        if title[:6] == "Annex ":
            key = title[6]
            listchunk += f"* [{title}](#{key})\n"
            nestinglevel = 0
        elif key is None:
            listchunk += f"* [{title}](#{title})\n"
            nestinglevel = 0
        else:
            level = key.count('.')
            line = f"* {key} [{mdformat(title)}](#{key})\n"
            if level:
                line = indent(line, level * 4)
            listchunk += line
    return titlechunk + "\n\n" + listchunk
