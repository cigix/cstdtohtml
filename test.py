#!/usr/bin/env python3

import subprocess
import sys

import pages
import utils
from abstract import Abstract
from toc import TOC, TOCMatcher

def pdftotext(file):
    '''pdftotext(file): Run the file through `pdftotext -layout`.

    If the subprocess fails, its stderr gets printed to stderr, and its return
    status is passed to sys.exit().

    Parameters:
        - file: str, path to the PDF file

    Return: str, stdout of the subprocess.'''
    process = subprocess.run(["pdftotext", "-layout", file, "-"],
                             capture_output=True, text=True)
    if process.returncode != 0:
        print(process.stderr, end='', file=sys.stderr)
        sys.exit(process.returncode)
    return process.stdout

def main(argv):
    text = pdftotext(argv[1])
    with open("test.txt", 'w') as f:
        f.write(text)
    #pages = list()
    #for i, page in enumerate(text.split('\f')):
    #    try:
    #        pages.append(Page(page))
    #    except:
    #        print(i, page)
    #        raise
    #pages.Page(text.split('\f')[374])
    #exit(42)
    unstructuredpages = [pages.Page(p) for p in text.split('\f') if p]
    for i in range(len(unstructuredpages)):
        with open(f"{i}.txt", 'w') as f:
            f.write('\n'.join(unstructuredpages[i].content))

    coverbegin = 0
    # The cover and the first page of content have a common subheader
    front_header = utils.groupwords(unstructuredpages[coverbegin].content[0])
    abstractbegin = coverbegin + 1
    while unstructuredpages[abstractbegin].content[0].lstrip() != "Abstract":
        abstractbegin += 1
    tocbegin = abstractbegin + 1
    while unstructuredpages[tocbegin].content[0].lstrip() != "Contents":
        tocbegin += 1
    forewordbegin = tocbegin + 1
    while unstructuredpages[forewordbegin].content[0].lstrip() != "Foreword":
        forewordbegin += 1
    introbegin = forewordbegin + 1
    while unstructuredpages[introbegin].content[0].lstrip() != "Introduction":
        introbegin += 1
    contentsbegin = introbegin + 1
    while (utils.groupwords(unstructuredpages[contentsbegin].content[0])
           != front_header):
        contentsbegin += 1
    bibliobegin = contentsbegin + 1
    while unstructuredpages[bibliobegin].content[0].lstrip() != "Bibliography":
        bibliobegin += 1
    indexbegin = bibliobegin + 1

    coverupages = unstructuredpages[coverbegin:abstractbegin]
    abstractupages = unstructuredpages[abstractbegin:tocbegin]
    tocupages = unstructuredpages[tocbegin:forewordbegin]
    forewordupages = unstructuredpages[forewordbegin:introbegin]
    introupages = unstructuredpages[introbegin:contentsbegin]
    contentsupages = unstructuredpages[contentsbegin:bibliobegin]
    biblioupages = unstructuredpages[bibliobegin:indexbegin]

    abstract = Abstract(abstractupages)
    toc = TOC(tocupages)
    tocmatcher = TOCMatcher(toc)

    # Structured pages
    cover = [pages.CoverPage(coverupages[0], tocmatcher)]
    cover += [pages.StructuredPage(p, tocmatcher) for p in coverupages[1:]]
    foreword = [pages.StructuredPage(p, tocmatcher) for p in forewordupages]
    intro = [pages.StructuredPage(p, tocmatcher) for p in introupages]
    contents = [pages.CoverPage(contentsupages[0], tocmatcher)]
    contents += [pages.StructuredPage(p, tocmatcher)
                 for p in contentsupages[1:]]
    biblio = [pages.StructuredPage(p, tocmatcher) for p in biblioupages]

    for p in contents:
        p.reindentcodes()

    #for p in contents:
    #    print(p)
    #    print()



if __name__ == '__main__':
    main(sys.argv)
