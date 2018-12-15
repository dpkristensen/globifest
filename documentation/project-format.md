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

## 3 Configuration Elements

### 3.1 Project Structure

**Parent**=Top

The "project" directive is used to start a block defining the structure.  Files which are only included in another project (i.e., as a layer variant) should not have this block.

The project must be followed by a human readable name.

Example:

    :project My Project
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

### 3.3 Package (NOT YET IMPLEMENTED)

**Parent**=project **Multiple**

The "package" directive defines the path to a manifest containing packages to include.  Ex:

    :package Utilities/core.gman
