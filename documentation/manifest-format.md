# Globifest - Manifests

Manifest files describe how to build and integrate your package into a project.

**Note:** Globifest's cross-platform compatibility is centered around support for Python, so many behaviors of the manifest are dependent upon the implementation of the interpreter.

Python 3.4 or greater is recommended.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 General Format

Manifest files are parsed in a mostly line-oriented fashion and should be encoded as ASCII.  Carriage Return (ASCII 13) and/or Line Feed (ASCII 10) both indicate a new line (so the format is agnostic to Unix or DOS-style line endings).

### 1.1 Comments

All lines leading with a Semicolon (ASCII 59) or Hash (ASCII 35) are not processed by the parser.  These can be used to communicate information to Humans, Software, or Robots reading the file, but should be ignored by the build system.

    ; This is a comment
    ; It will be ignored by the parser
    # This is also a comment
        ; Comments can be indented, too!

Comments are not allowed at the end of a line containing other manifest content.

### 1.2 Parenthases

Some lines use parentheses to specify additional information.  In that case, the parentheses do not need to be co-located on the line which starts the command; but only whitespace is allowed to separate the identifier, parenthases, and the content which follows.

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

Content is NOT allowed after the closure:

    :identifier( ... ) <Cannot put stuff here!>

### 1.3 Directives

A directive is a special identifier following a leading Colon (ASCII 58).  These are used to indicate information about the lines to follow.  The lines between related directives form a block.

### 1.4 Leading Whitespace

Leading whitespace is ignored on all lines.  This allows authors to use whatever style suits their needs; however, manifests should be formatted to enhance readability for Human readers.

See [guidelines.md](guidelines.md) for recommended guidelines.

### 1.5 Global Parameters (NOT YET IMPLEMENTED)

Lines beginning with "@" are used to specify global parsing parameters:

    @version <number>

The version is intended for backwards compatibility of breaking changes, if needed in the future.  If ommitted, the version number is assumed to be 1.

To support adding more parameters later, unknown parametes are ignored when the version is greater than the parser's version.

## 2 Entries and Labels

An entry is simply a single element that can be processed in a certain context; these are generally passed to the build system, such as a source file or a definition.

Labels define what type of entries follow, and ultimately where the output goes.  The following sections define what labels are allowed and what type of entries they contain.

*IMPORTANT*:

1. The last label processed in a block is applied to all entries that follow, except that nested blocks may override the label for the duration of the block.

2. The file itself is considered a block, for all practical purposes.

### 2.1 aux_files

Auxiliary files that are part of the project, but not built into the end-user deliverable.

### 2.2 prv_defines

Definitions to be passed to the compiler for the files referenced in this manifest.

### 2.3 prv_includes

Include directories to be passed to the compiler for the files referenced in this manifest.

### 2.4 pub_defines

Definitions to be passed to the compiler for the files referenced in this manifest, and any other files which depend on this manifest.

*USE WITH CARE:* Allowing a package to add defines for the whole system is not a common practice, so the names should be unique within any possible build environment.  Normally definitions should be in a public header file.  See [guidelines.md](guidelines.md) for recommended guidelines.

### 2.5 pub_includes

Include directories to be passed to the compiler for the files referenced in this manifest, and any other files which depend on this manifest.

### 2.6 sources

Files which are to be used as primary inputs to any build step (compiling, or any other transformative operation).

## 3 Conditional Entries

Conditional entries use the directives "if", "elif", "else", "end" following form:

    :if( <condition> )
        <entries>
    :elif( <condition> )
        <entries>
    :else
        <entries>
    :end

The following rules apply:

* :if is followed by a () section.
* :elif is followed by a () section.
* :elif is optional; but if used, it must appear after :if.
* :elif directives may be used multiple times with different conditions.
* :else is optional; but if used, it must appear after :if and any :elif directives.
* :else is considered a matched condition only if none of the previous conditions have matched.
* After a condition is matched, the entries that follow in that block are used; subsequent conditions are not evaluated and subsequent entries are ignored until :end.

### 3.1 Conditional Expressions

Conditional expressions are documented in [conditionals.md](conditionals.md).

### 3.2 Nesting

These can also be nested within each other:

    :sources
    :if( a = 1 )
        foo.c
        :if( b = 1 )
            :sources
                baz.c
            :pub_includes
                ./headers/baz
        :end
        bar.cpp
    :end

Note the change in labels; the label is restored to the previous (sources) upon exiting the inner block.

Any other type of block can be nested within this level as well.

## 4 Switched Entries (NOT YET IMPLEMENTED)

Switched entries use the directives "switch", "case", "default", "end" following form:

    :switch( <identifier or value> )
        ; No entries are allowed here
    :case( <identifier or value> )
        <entries>
    :default
        <entries>
    :end

The following rules apply:

* :switch is followed by a () section.
* :case is followed by a () section.
* :case is optional.
* :case directives may be used multiple times with different values.
* :default is optional; but if used, it must appear after :switch and any :case directives.
* :default is considered a matched value only if none of the previous values have matched.
* After a value is matched, the entries that follow in that block are used; subsequent values are not evaluated and subsequent entries are ignored until :end.

### Nesting

Switchd entries can be nested:

    :switch( a )
    :case( 1 )
        Custom1/Backend.java
        :switch( b )
        :case
    :default
        Default/Backend.java
    :end

## 5 Globbing (NOT YET IMPLEMENTED)

To add files via Unix-style wildcard matching, use the "g" or "glob" directives:

    ; g globs a single expression, which follows on the same line
    :g *.txt

    ; glob starts a block where all entries in the block are glob expressions
    :glob
        *.cfg
        *.ini
    :end

See [Python API for glob()](https://docs.python.org/2/library/glob.html) for details about pattern matching.

## 6 Sub-Manifests and Configuration (NOT YET IMPLEMENTED)

Splitting up manifests for large or complex code bases can make maintenance easier.

### 6.1 Including Manifests

The "include" directive will import another file as if the directive was literally replaced with the contents of the file, using the following form:

    :include <filename>

This can appear multiple times.

### 6.2 Configuration Files

The "config" directive will specify that this manifest uses the given configuration file.

    :config <filename>

This can appear multiple times.

## 7 Packaging (NOT YET IMPLEMENTED)

Packaging is a multi-purpose feature which enables:

* Isolation of sources not designed to be built together
* More granular control over output generation
* Use as an easy top-level control for building a large code base with multiple packages.

To have more fine-tune control over how a manifest is included, it can be imported as a separate package with the "package" directive block with the following form:

    :package [<name>]
        :config <filename>
        :cout <path>
        :manifest <filename>
        :mout <path>
        :hdr_include <path>
        :out_include <path>
    :end

All paths, unless absolute, are relative to the manifest file location.  Usage of the parameters is detailed below:

* :config - Specifies a config file to use
  * Can specify multiple
* :cout - Overrides the output directory for config files
  * Up to one per block
* :manifest - Sets the manifest to include
  * Can specify multiple
* :mout - Controls the output directory or filename
  * Up to one per block
* :hdr_include - Allows manual specification of directories relative to this file
  * Can specify multiple
  * Intended for source headers in the package
* :out_include - Allows manual specification of directories relative to the output path
  * Can specify multiple
  * Intended for headers generated by the configurations

Additional rules:

* All parameters are optional (although nothing happens if empty).
* When recursing into manifests:
  * Relative directory settings are applied recursively.
* If a package name is specified, all output files are directed to a sub-folder, and relative path   settings are applied afterward.
* These parameters can be controlled conditionally as well (:if, :switch).

Examples:

    :package
        ; Imports a configuration and the headers generated by it
        :config my_configs.cfg
        :out_include .
    :end

    :package external/foo
        ; Foo does not supply a globifest package, so we provide one
        ; When output is directed to _Output globally, the files will appear in
        ;   _Output/external/foo/config/<generated headers>
        ;   _Output/external/foo/<compiled objects>

        :config modules/external/foo.cfg
        :cout config
        :out_include config
        :manifest modules/external/foo.mfg
    :end
