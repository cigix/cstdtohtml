# How to contribute to cstdtohtml

## Testing process

The Makefile assumes you have a file called `c23.pdf` at the root of the
repository, which is used by most rules; you will need to either rename your
file or edit the Makefile to change that.

### Step 0: Resetting the ref

```
make new_ref
```
This will reset the ref to the current state of the generation.

### Step 1: Identify a problem

Pinpoint a bit of the generated HTML that is wrong, either visually, in the code
structure, or compared to the ref. Find that same text in the file
`.cstdtohtml_raw`, which is a representation of what the main program loop
manipulates.

### Step 2: Fix the problem

Edit the code so that the problem gets fixed. You can use
```
make [HTML]
```
to generate `c23.html` from `c23.pdf`, or `[whatever].html` to generate it from
`[whatever].pdf`.

### Step 3: Check for regressions

Run
```
make check
```
to compare the new generation to the ref. Check in the diff that only the
problem you pinpointed is changed, and nothing else, otherwise go back to Step
2. The new generation is truncated to match the lines of the ref, so you might
get some unmatched lines at the end.

### Step 4: Commit

Once you:

* have fixed your problem,
* have checked for regressions,

you may commit your changes. You now need to update the ref: go back to Step 0.

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

# Future development

For version 1, the idea is to iterate over what is already there to provide a
better translation.

For version 2, there will be an actual parser that iterates over intermediate
representations of the document, to make an accurate reproduction.
