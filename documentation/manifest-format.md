# Globifest - Manifests

Manifest files describe how to build and integrate your package into a project.

**Note:** Globifest's cross-platform compatibility is centered around support for Python, so many behaviors of the manifest are dependent upon the implementation of the interpreter.

## Format

Manifest files should be encoded as ASCII.

### Definitions

* **Bounding Symbols** - Characters marking the beginning and end of a special section: Parenthases (ASCII 40 and 41), Braces (ASCII 123 and 125), and Quotes (ASCII 34)
* **Newline** - A sequence of character(s) which separate lines in the file: CR (ASCII 13) or CR+LF( ASCII 13 followed by ASCII 10).
* **Section** - A sequence of entries within Bounding Symbols.  The whole file is considered a section as well.
* **Whitespace** - Spaces and tabs at the beginning and end of a line, around directives and Bounding Symbols

### Comments

All lines leading with a Semicolon (ASCII 59) are not processed by the parser.  These can be used to communicate information to Humans or Robots reading the file, but should be ignored by the build system.

    ; This is a comment
    ; It will be ignored by the parser

### Blocks

A group of statements can be grouped by bounding symbols.

#### Grouping entries

Braces can be used to create a group of entries.  Naturally, this is less efficient; it serves no functional purpose by itself over leaving the entries unbounded.

But these types of groups are used with conditionals (described later).

#### Spacing of blocks

Some entries use parentheses to specify additional information.  In that case, the parentheses do not need to be co-located on the line which starts the command; but only whitespace is allowed to separate the identifier, bounding symbols, and the entries within the section.

For example, all of the following are equivalent forms:

    :identifier( ... )
    :identifier(
        ...
        )
    :identifier
        (
        ...
        )
    :identifier
        (
        ... )
    :identifier ( ...
        )

### Directives

A directive is a special identifier following a leading Colon (ASCII 58).  These are used to indicate information about the lines to follow in the Section.

#### Labels

Labels define what type of entries follow, and ultimately where the output goes.  Allowed labels are:

##### aux_files

Auxiliary files that are part of the project, but not built into the end-user deliverable.

##### prv_defines

Definitions to be passed to the compiler for the files referenced in this manifest.

##### prv_includes

Include directories to be passed to the compiler for the files referenced in this manifest.

##### pub_defines

Definitions to be passed to the compiler for the files referenced in this manifest, and any other files which depend on this manifest.

*USE WITH CARE:* Allowing a package to add defines for the whole system is not a common practice, so the names should be unique within any possible build environment.  Normally definitions should be in a public header file.  But this could be used, for example, to declare features provided by the package where a header file didn't previously exist.

##### pub_includes

Include directories to be passed to the compiler for the files referenced in this manifest, and any other files which depend on this manifest.

##### sources

Files which are to be used as primary inputs to any build step (compiling, or any other transformative operation).

#### Conditional Entries

Conditional entries use the directives "if", "elif", "else", "end" following form:

    :if( <condition> )
    {
        <entries>
	:elif( <condition> )
        <entries>
    :else
        <entries>
    }

The following rules apply:

* :if is followed by a () section, followed by a \{\} section.
* :elif is followed by a () section.
* :elif is optional; but if used, it must appear after :then.
* :else is optional; but if used, it must appear after :then (and all :elif, if present as well).
* :elif directives may be used multiple times

These can also be nested within each other:

    :if( a=1 )
    {
        :sources
        foo.c
        :if( b = 1 )
        {
            :sources
            baz.c
        }
    }


#### Globbing files

To add files via Unix-style wildcard matching, use glob:

    :glob(*.txt)
    :glob(
        *.cfg
        *.ini
        )

Multiple files may be specified, but still one pattern per line.

See [Python API for glob()](https://docs.python.org/2/library/glob.html) for details about pattern matching.
