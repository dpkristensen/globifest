# Globifest - Configuration

Configuration files store the selected options to use when building your project.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 Project Configuration Structure

Each project may have multiple axes upon which to define all build configurations.  Each project has one or more "layers", which each have one or more "variants".

Only one variant may be selected at a time per layer, but multiple layers may exist.

The configuration values can be overridden by higher-priority layers.  The lowest-priority layer is implicitly defined as the "default" layer.

Consider the following configuration example:

* Layer "default" (implicitly exists)
* Layer "compiler" = {"gcc", "msvc", "arm"}
* Layer "mode" = {"production", "development"}

Permutating all values above (1 default x 3 compilers x 2 modes), there are a total of **6 possible build variations per project**.

The "default" layer is the lowest priority, followed by "compiler", and then "mode" is the highest.  The effective configuration is found by first applying default, then compiler, then mode.

### 1.1 File Heirarchy

The configuration file is the top-level project, and only contains the "default" implicit layer settings.  Settings for all other layers are stored in a separate file, one for each variant of that layer.

So the folder structure might look like this:

* /my-project/config/build.gconf
* /my-project/config/build_compiler_arm.cfg
* /my-project/config/build_compiler_gcc.cfg
* /my-project/config/build_compiler_msvc.cfg
* /my-project/config/build_mode_development.cfg
* /my-project/config/build_mode_production.cfg

### 1.1 Configuration Sharing Between Projects

A "project" can't inherit from another project, but it can re-use the same configuration files.  Let's say in addition to a hardware build, you want to also define a configuration for a program to run automated tests (which only needs to work on Windows and Linux).

So the configuration for this test program would look like:

* Layer "default" (implicitly exists)
* Layer "compiler" = {"gcc", "msvc"}
* Layer "os" = {"posix", "win32"}

Now you could build with gcc for both os variants, but msvc can't be used to generate posix applications.  So this combination is prohibited.

Restructuring the project for both the hardware and test app build, you might have something like this.

* /my-project/config/compiler/arm.cfg
* /my-project/config/compiler/gcc.cfg
* /my-project/config/compiler/msvc.cfg
* /my-project/config/mode/development.cfg
* /my-project/config/mode/production.cfg
* /my-project/config/os/posix.cfg
* /my-project/config/os/win32.cfg
* /my-project/config/build_hardware.gconf
* /my-project/config/build_tests.gconf

build_hardware.gconf needs to use:

* compiler/arm.cfg
* compiler/gcc.cfg
* compiler/msvc.cfg
* mode/development.cfg
* mode/production.cfg

build_tests.gconf needs to use:

* compiler/gcc.cfg
* compiler/msvc.cfg
* os/posix.cfg
* os/win32.cfg

If desired, you could add stub layers with a single value for consistency about where the configs are stored.  Examples:

* Using os/rtos.cfg for the hardware build makes the "OS" settings stored consistently in a separate file, instead of directly in build_hardware.gconf.
* Using mode/development.cfg for the tests build prevents the need to repeat the same settings for tests.

### 1.2 Configuration Inheritance

Inheriting another configuration file would be directly including one file into another, which is not supported.

This is because the configuration app modifies the files when saving and uses the layer variant to determine where to save settings.  Direct inclusion would make the target file ambiguous.

To implement similar functionality, define a layer with a single variant and point it to the file you wish to include.

## 2 General Format

Configuration files are parsed in a mostly line-oriented fashion and should be encoded as ASCII.  Carriage Return (ASCII 13) and/or Line Feed (ASCII 10) both indicate a new line (so the format is agnostic to Unix or DOS-style line endings).

It is recommended that the filename end in .cfg or .gconf.

NOTE: The provided application will generate and modify these files for users, but they can be created/modified manually or via a different application as well.

### 2.1 Comments

All lines leading with a Semicolon (ASCII 59) or Hash (ASCII 35) are not processed by the parser.  These can be used to communicate information to Humans, Software, or Robots reading the file, but should be ignored by the configuration interface.

    ; This is a comment
    ; It will be ignored by the parser
    # This is also a comment
        ; Comments can be indented, too!

Comments are not allowed at the end of a line containing other manifest content.

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

The "layer" directive defines a configuration layer with a higher priority than all previously defined layers (or higher than the "default" layer if none previously defined).

The layer must be followed by an identifier, which will serve as its name.  This cannot be "default".

Example:

    :layer compiler
        variant arm
        variant gcc
        variant msvc
    :end

The files produced by this structure in "build.gconf" would be:

* build_compiler_arm.cfg
* build_compiler_gcc.cfg
* build_compiler_msvc.cfg

#### 3.2.1 Variant Parameter

**Parent**=layer **Mandatory** **Multiple**

The "variant" parameter is followed by an identifier, which names one possible value for the layer.

#### 3.2.2 File Prefix Parameter

**Parent**=layer

The "prefix" parameter contains the relative path to the files containing settings for each variant.

If omitted, the base filename of the project's config file is used:

    <basename>_<layer>_

Example:

    :layer os
        variant posix
        variant win32
        prefix os/
    :end

The files produced by this structure in "build.gconf" would be:

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

The files produced by this structure in "build.gconf" would be:

* build_os_posix.txt
* build_os_win32.txt

##### 3.2.3.1 No Suffix

The value of "none" is handled specially to omit the suffix entirely.

Example:

    :layer os
        variant posix
        variant win32
        suffix none
    :end

The files produced by this structure in "build.gconf" would be:

* build_os_posix
* build_os_win32

### 3.3 Settings

**Parent**=Top **Multiple**

Settings are stored one on each line as a simple key/value pair with whitespace ignored:

    [whitespace]identifier=value[whitespace]

These do not need to be enclosed in a directive block, but are usually placed after the project directive.

The identifier corresponds to the definition file, and the value is user-supplied.

Example:

    MYMODULE_ENABLED=TRUE
    MYMODULE_FEATURE1_TEXT=This is a cool feature!

The acceptable input for value is dependent upon the input type.
