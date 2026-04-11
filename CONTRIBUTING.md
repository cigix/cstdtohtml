# How to contribute to cstdtohtml

## Testing process

For legal reasons, we can only do regression testing on real C Standard Draft
PDF files. Moreover, for the same legal reasons, test cases cannot be shipped
with the test suite. See [tests/README.md].

### Step 0: Populating the test suite

Place C Standard Draft PDF files in `tests/in/`, then run `make ref -j`. This
will produce the reference files that will later be compared to.

### Step 1: Identify a problem

Pinpoint a bit of the generated HTML or Markdown that is wrong, either visually,
in the code structure, or compared to the PDF.

To help identify the problem, you can uncomment the lines in `cstdtohtml` that
refer to `.cstdtohtml_raw`: once uncommented, they will output a file containing
the raw text output of `pdftotext`, which is the representation that the main
program starts from.

### Step 2: Fix the problem

Edit the code so that the problem gets fixed. You can use:
```bash
make [HTML or MD]
```
to generate `[whatever].html` or `[whatever].md` from `[whatever].pdf`. If you
don't specify a file, the default is to generate `c23.html`.

### Step 3: Check for regressions

Run:
```bash
make check -j
```
to compare the new generation to the ref. Check in the diff that only the
problem you pinpointed is changed, and nothing else, otherwise go back to Step
2.

### Step 4: Commit

Once you:

* have fixed your problem,
* have checked for regressions,

you may commit your changes.

### Step 5: Repeat

Make the current output your new ref:
```bash
make ref -j
```
then start back from Step 1.

## Scope of the project

This project is a best effort to provide tools for the community. You should not
go over the top to fix something that is still readable and usable. There are
currently a lot of issues linked to how `pdftotext` restitutes the original
formatting, and the rules for parsing everything correctly are stepping on top
of each other, so do not hesitate to consider as WONTFIX anything that is not
critical.

What is critical:

* Links, anchors and titles. It is essential that users get to properly navigate
  and understand where they are in the hundreds of pages of the standard.
* Readability. Sometimes the formatting makes the tool generate strange stuff,
  so here's the rule of thumb: whenever users read something, they should either
  understand the same thing as the standard, or understand there's a formatting
  error and that they should check the actual standard.
