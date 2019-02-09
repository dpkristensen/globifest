# Globifest - Manifests

Manifest files describe how to build and integrate your package into a project.

**Note:** Globifest's cross-platform compatibility is centered around support for Python, so many behaviors of the manifest are dependent upon the implementation of the interpreter.

Python 3.4 or greater is recommended.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 General Format

Manifest files are parsed in a mostly line-oriented fashion and should be encoded as ASCII.  Carriage Return (ASCII 13) and/or Line Feed (ASCII 10) both indicate a new line (so the format is agnostic to Unix or DOS-style line endings).

It is recommended that the filename end in .mfg or .gman.

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

### 1.5 Requirements, Constraints, and Features

For each element, tags may be listed in bold at the top of the section:

* Follows - This element must appear after all of the given elements listed here when used in the same block.
* Parent - This element must be a child of one of the following directives listed here; "Top" means it can be a top-level element of the file.  "Any" means any element _that does not take Parameters_.
* Mandatory - This element must appear at least once within the block.
* Multiple - One or more elements may appear in the same block.
* Parameters - This block has parameter elements, which are documented in a related section.

Unless otherwise specified, all elements are unique within the block (cannot be defined twice).

### 1.6 Identifier Naming

An identifier is a symbolic name for the element.  It must only include one or more characters of the set {a-z,A-Z,0-9,_}, no whitespace is allowed

## 2 Entries and Labels

An entry is simply a single element that can be processed in a certain context; these are generally passed to the build system, such as a source file or a definition.

Labels define what type of entries follow, and ultimately where the output goes.  The following sections define what labels are allowed and what type of entries they contain.

*IMPORTANT*:

1. The last label processed in a block is applied to all entries that follow, except that nested blocks may override the label for the duration of the block.

2. The file itself is considered a block, for all practical purposes.

### 2.1 aux_files

**Parent**={Any} **Multiple**

Auxiliary files that are part of the project, but not built into the end-user deliverable.

### 2.2 prv_defines

**Parent**={Any} **Multiple**

Definitions to be passed to the compiler for the files referenced in this manifest.

### 2.3 prv_includes

**Parent**={Any} **Multiple**

Include directories to be passed to the compiler for the files referenced in this manifest.

### 2.4 pub_defines

**Parent**={Any} **Multiple**

Definitions to be passed to the compiler for the files referenced in this manifest, and any other files which depend on this manifest.

*USE WITH CARE:* Allowing a package to add defines for the whole system is not a common practice, so the names should be unique within any possible build environment.  Normally definitions should be in a public header file.  See [guidelines.md](guidelines.md) for recommended guidelines.

### 2.5 pub_includes

**Parent**={Any} **Multiple**

Include directories to be passed to the compiler for the files referenced in this manifest, and any other files which depend on this manifest.

### 2.6 sources

Files which are to be used as primary inputs to any build step (compiling, or any other transformative operation).

## 3 Conditional Entries

**Parent**={Any} **Multiple**

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

Conditional expressions are documented in [conditionals.md](conditionals.md).

## 4 Switched Entries (NOT YET IMPLEMENTED)

**Parent**={Any} **Multiple**

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

## 5 Globbing

To add files via Unix-style wildcard matching, use the "g" or "glob" directives:

    ; g globs a single expression, which follows on the same line
    :g *.txt

    ; glob starts a block where all entries in the block are glob expressions
    :glob
        *.cfg
        *.ini
    :end

See [Python API for glob()](https://docs.python.org/2/library/glob.html) for details about pattern matching.

## 6 Including Files

**Parent**={Any} **Multiple**

Splitting up manifests for large or complex code bases can make maintenance easier.

The "include" directive will import another file as if the directive was literally replaced with the contents of the file, using the following form:

    :include <filename>

File paths encountered in the include file will be treated as relative to the included file.  Included files may include other files as well.

It is recommended that included files that contain manifest content use the extension ".gmi" to indicate it contains content for inclusion into a manifest file (as opposed to other types of Globifest content).

## 7 Configuration Definitions

**Parent**={Top} **Parameters**

The "config" directive block is used to include definition files, and control output generation.  Example:

    :config
        definition config.gdef
        generate C my_project/config.h
    :end

### 7.1 Definition Parameter

**Parent**=config **Mandatory**

The "definition" parameter indicates what definition file to use for this block, of the form:

    definition <filename>

The _filename_ parameter is relative to the manifest file, unless an absolute path is given.

### 7.2 Generating Output Files

**Parent**=config **Multiple** **Follows**=definition

The "generate" parameter generates a file with the given name and format containing all the settings in the definition file.  Multiple output files can be generated, if needed for multiple languages.

The form of this line is:

    generate <format> <filename>

Supported formats (case-insensitive) include:

* C - Compliant to ISO 9899:1990 (aka C89/C90)
* Java - Compliant to "The Java Language Specification" ISBN 0-201-63451-1 (aka Java 1.0).
  * For Java, the path name will ultimately end up being used to determine the package name.

Examples:

    :config
        ; These definitions are only available in manifest conditional logic
        :definition my_configs.dfg
    :end

    :config
        ; These definitions are available in manifest conditional logic as
        ; well as in the files specified.
        definition settings.gdef

        generate C my_module/settings.h

        ; Package is com.my_company.component
        ; Class name is Settings
        ; The file name will be converted to lowercase per Java convention
        generate Java com/my_company/component/Settings.java
    :end

Although additional formats can be registered externally with `GlobifestLib.Generators.register_generator`, usage or overwriting of the format `_custom` is prohibited.

### 7.3 Generating Custom-Format Output Files

**Parent**=config **Multiple** **Follows**=definition

The "generate_s" parameter generates a file with the given name containing all the settings in the definition file, but generated by a custom script.  Multiple output files can be generated, if needed for multiple languages.

The form of this line is:

    generate_s <script_filename> <out_filename>

`script_filename` must point to a python script.

Example:

    :config
        definition settings.gdef
        generate_s generators/xml.py my_module/settings.xml
        generate_s generators/json.py my_module/settings.json
    :end

The above example will pass the settings defined by settings.gdef to the scripts given (path relative to the manifest) to generate the corresponding files (path relative to the output directory).

The python module will be set up with the following properties:

* `__name__` = "<globifest"
  * This allows alternate invocation methods of the script
* `DEFINITIONS` = A list of `GlobifestLib.Util.Container` objects containing the following keys:
  * `param` = A `GlobifestLib.DefTree.Parameter` object describing the parameter
  * `value` = The object's value (class is dependent upon the parameter type; ex: `int`, `float`, `string`, `bool`...)
* `OUT_FILE` = Absolute path to target file
* `OUT_DIR` = Absolute path to the output directory of the package
  * **This is not necessarily the same as the parent directory of** `OUT_FILE`
* `PARAM_TYPE` = The `GlobifestLib.DefTree.PARAM_TYPE` enumeration.  This can be used in conjunction with the parameter type:
  * Use the `.enum_id` table to convert the type to the Globifest data type string
  * Compare the type to apply special formatting
* `g_print(msg)` = A function to log messages to the build output
* `g_debug(msg)` = A function to log debug messages to the build output (visible at higher verbosity levels)
* `g_err(msg)` = A function to raise an exception (just like `GlobifestLib.Log.E`) with a build error message.

Other changes to Python's `sys` library properties may be applied, depending on the interpreter version.

An example script is shown below, illustrating the use of the `module.__name__` property to detect multiple invocation contexts:

    if __name__ == "<globifest>":
        g_print("Generating file: {}".format(OUT_FILE))

    if __name__ == "__main__":
        print("This is being run directly from the command line or interactive interpreter")
