# Globifest - Project

Project files store information necessary to build one or more software targets under various configurations.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 Project Configuration Structure

Each project may have multiple axes upon which to define all build configurations.  Each project has one or more "layers", which each have one or more "variants".

Only one variant may be selected at a time per layer, but multiple layers may exist.  The configuration values can be overridden by higher-priority layers, and a layer may also only have one variant (useful for establishing overridable defaults)

Consider the following configuration example:

* Layer "base" = {"defaults"}
* Layer "compiler" = {"gcc", "msvc", "arm"}
* Layer "mode" = {"production", "development"}

Permutating all values above (1 base x 3 compilers x 2 modes), there are a total of **6 possible build variations per project**.

The "base" layer is the lowest priority, followed by "compiler", and then "mode" is the highest.  The effective configuration is found by first applying base, then compiler, then mode.

### 1.1 File Heirarchy

A project must have at least one layer and settings for all layers are stored in a separate file, one for each variant of that layer.

So the folder structure might look like this:

* /my-project/config/base_defaults.cfg
* /my-project/config/build.gproj
* /my-project/config/compiler_arm.cfg
* /my-project/config/compiler_gcc.cfg
* /my-project/config/compiler_msvc.cfg
* /my-project/config/mode_development.cfg
* /my-project/config/mode_production.cfg

### 1.1 Configuration Sharing Between Projects

A "project" can't inherit from another project, but it can re-use the same configuration files.  Let's say in addition to a hardware build, you want to also define a configuration for a program to run automated tests (which only needs to work on Windows and Linux).

So the configuration for this test program would look like:

* Layer "base" {"test_defaults"}
* Layer "compiler" = {"gcc", "msvc"}
* Layer "os" = {"posix", "win32"}

Now you could build with gcc for both os variants, but msvc can't be used to generate posix applications.  So this combination is prohibited.  So when adding a tests project, the overall file structure would look like:

* /my-project/config/base_hardware_defaults.cfg
* /my-project/config/base_test_defaults.cfg
* /my-project/config/build_hardware.gproj
* /my-project/config/build_tests.gproj
* /my-project/config/compiler_arm.cfg
* /my-project/config/compiler_gcc.cfg
* /my-project/config/compiler_msvc.cfg
* /my-project/config/mode_development.cfg
* /my-project/config/mode_production.cfg
* /my-project/config/os_posix.cfg
* /my-project/config/os_win32.cfg

build_hardware.gproj needs to use:

* hardware-defaults.cfg
* compiler_arm.cfg
* compiler_gcc.cfg
* compiler_msvc.cfg
* mode_development.cfg
* mode_production.cfg

build_tests.gproj needs to use:

* base_test_defaults.cfg
* compiler_gcc.cfg
* compiler_msvc.cfg
* os_posix.cfg
* os_win32.cfg

If desired, you could add stub layers with a single value for consistency about where the configs are stored.  Examples:

* Using os_rtos.cfg for the hardware build makes the "OS" settings stored consistently in a similar layer as other OS settings.
* Using mode_development.cfg for the tests build prevents the need to repeat the same settings for tests.

## 2 General Format

Project files are parsed in a mostly line-oriented fashion and should be encoded as ASCII.  Carriage Return (ASCII 13) and/or Line Feed (ASCII 10) both indicate a new line (so the format is agnostic to Unix or DOS-style line endings).

It is recommended that the filename end in .pfg or .gproj.

NOTE: The provided application will generate and modify these files for users, but they can be created/modified manually or via a different application as well.

### 2.1 Comments

All lines leading with a Semicolon (ASCII 59) or Hash (ASCII 35) are not processed by the parser.  These can be used to communicate information to Humans, Software, or Robots reading the file, but should be ignored by most tools.

    ; This is a comment
    ; It will be ignored by the parser
    # This is also a comment
        ; Comments can be indented, too!

Comments are not allowed at the end of a line containing other content.

### 2.2 Directives

A directive is a special identifier following a leading Colon (ASCII 58).  These are used to indicate information about the lines to follow.  The lines between related directives form a block.  Most directive blocks are closed by the "end" directive unless otherwise stated.

### 2.3 Requirements, Constraints, and Features

For each element, tags may be listed in bold at the top of the section:

* Parent - This element must be a child of one of the following directives listed here; "Top" means it can be a top-level element of the file.
* Mandatory - This element must appear at least once within the block.
* Multiple - One or more elements may appear in the same block.
* Parameters - This block has parameter elements, which are documented in a related section.

Unless otherwise specified, all elements are unique within the block (cannot be defined twice).

### 2.4 Parameter Elements

Within some entries there may be parameters (one on each line) of the form:

    [whitespace]parameter value[whitespace]

Note that trailing whitespace is ignored.

### 2.5 Identifier Naming

An identifier is a symbolic name for the element.  It must only include one or more characters of the set {a-z,A-Z,0-9,_}, no whitespace is allowed

## 3 Configuration Elements

### 3.1 Project Structure

**Parent**=Top

The "project" directive is used to start a block defining the structure, and must be followed by an identifier (which is the name of the project).

Example:

    :project MyProject
        # ... project contents go here
    :end

### 3.2 Layer

**Parent**=project **Multiple**

The "layer" directive defines a configuration layer with a higher priority than all previously defined layers.  The layer must be followed by an identifier, which will serve as its name.

Example:

    :layer compiler
        variant arm
        variant gcc
        variant msvc
    :end

The files produced by this structure in "build.gproj" would be:

* compiler_arm.cfg
* compiler_gcc.cfg
* compiler_msvc.cfg

#### 3.2.1 Variant Parameter

**Parent**=layer **Mandatory** **Multiple**

The "variant" parameter is followed by an identifier, which names one possible value for the layer.

#### 3.2.2 File Prefix Parameter

**Parent**=layer

The "prefix" parameter contains the relative path to the files containing settings for each variant.  If omitted, the default is:

    <layer>_

Example:

    :layer os
        variant posix
        variant win32
        prefix os/
    :end

The files produced by this structure would be:

* os/posix.cfg
* os/win32.cfg

#### 3.2.3 File Suffix Parameter

**Parent**=layer

The "suffix" parameter is appended to the name of files when generating layer variants.

If omitted, the default value of ".cfg" is used.

Example:

    :layer os
        variant posix
        variant win32
        suffix .txt
    :end

The files produced by this structure would be:

* os_posix.txt
* os_win32.txt

##### 3.2.3.1 No Suffix

The value of "none" is handled specially to omit the suffix entirely.

Example:

    :layer os
        variant posix
        variant win32
        suffix none
    :end

The files produced by this structure would be:

* os_posix
* os_win32

### 3.3 Package

**Parent**=project **Multiple**

The "package" directive defines the path to a manifest containing packages to include.  Ex:

    :package Utilities/core.gman

### 3.4 External Dependencies

**Parent**=project **Multiple**

The ":dependency" directive starts a parameterized block describing how to fulfill an external build-time dependency.  The directive must be followed by an identifier, which serves as a unique name.  Each parameter in the section is a set of actions which are followed in a chain to fulfill the dependency.  Ex:

    :dependency googletest
        dest googletest.zip
        url https://github.com/google/googletest/archive/release-1.8.0.zip
        sha256 F3ED3B58511EFD272EB074A3A6D6FB79D7C2E6A0E374323D1E6BCBCC1EF141BF
        extract googletest-release-1.8.0\
    :end

In the above example:

* The file will be downloaded from the given URL as googletest.zip.
* The zip file will be hashed with SHA256 and compared to the given hash.
* The zip file will be extracted with "googletest-release-1.8.0\" removed from the output path names.

Action names are not case sensitive, but must always be followed by an argument.

The components of an action are:

* Identifier - The keyword used to describe the action (ex: "dest")
* Argument - The text following the identifier (ex: "googletest.zip")
* Inputs - The inputs to an action are the outputs of the previous action; the first action in the sequence has no inputs.
* Outputs - The outputs of an action are the transformation of the input defined by the action; they will be used as inputs to the next action in the chain.

#### Destination Action

Supplies an input for the next command.

* Identifier: dest
* Argument: any text (dependent upon what the next action's Input requires)
* Inputs: None
* Outputs: The argument text

#### Extract Action

Extracts files from an archive.

* Identifier: extract
* Argument: Prefix text to remove from the destination file names, or . for no replacement.  Files which do not have the prefix will not be extracted.
* Inputs: The archive file name
* Outputs: The folder where all files were extracted to

#### Hash Action

Evaluates the hash of a file.

Note: To generate the hash, it is suggested to use "Get-FileHash" command in Power Shell (Windows) or any number of other tools supported by your machine (ex: sha256sum).

* Identifier: \<algorithm\>
* Argument: The expected result in hex (case-insensitive)
* Inputs: The input file name
* Outputs: The input file name

Supported algorithms:

* sha256

#### URL Download

Downloads a file from a URL

* Identifier: url
* Argument: The URL to download from (https recommended!)
* Inputs: The destination file name
* Outputs: The destination file name

### 3.5 Local Package

**Parent**=project **Multiple**

The "lcl_package" directive defines a _locally-defined_ manifest to use with a dependency.  Ex:

    :lcl_package <package_id> <path>

* package_id - the package name used in the dependency
* path - The path relative to the project file (or absolute) to the manifest file.

Example using a FOO module that does contains a manifest:

    :dependency FOO
        dest foo.zip
        url https://myserver.com/foo-1.0.zip
        extract foo-1.0/
    :end
    lcl_package FOO external/foo.gman
    ; The manifest is in a local folder /external
    ; When built in /_Output directory, the paths in the manifest will be relative to /_Output/FOO

And the manifest file might look like:

    :sources
        ; Files are available after the extract command
        extract/*.c

### 3.6 External Package

**Parent**=project **Multiple**

The "ext_package" directive defines an _externally-defined_ manifest that is supplied with a dependency.  Ex:

    :ext_package <package_id> <path>

* package_id - the package name used in the dependency
* path - The path relative to the dependency's output directory (or absolute) to the manifest file.

Below are functionally equivalent ways to use a FOO module that contains a manifest in the archive as "foo-1.0_/manifest.gman"

#### Example with path replacement

    :dependency FOO
        dest foo.zip
        url https://myserver.com/foo-1.0.zip
        extract foo-1.0/
    :end
    ext_package FOO extract/manifest.gman
    ; When built in /_Output directory, the path will be /_Output/FOO/extract/manifest.gman

#### Example without path replacement

    :dependency FOO
        dest foo.zip
        url https://myserver.com/foo-1.0.zip
        extract .
    :end
    ext_package FOO extract/foo-1.0/manifest.gman
    ; When built in /_Output directory, the path will be /_Output/FOO/extract/foo/manifest.gman

This form might be easier to use if a dependency provides multiple manifests in a form where usage of a prefix is infeasible.  But the folder name contains a version number, which will be repeated in each ext_package entry.
