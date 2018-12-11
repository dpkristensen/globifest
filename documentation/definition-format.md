# Globifest - Definitions

Definition files describe what options are available to configure your project.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 General Format

Definition files are parsed in a mostly line-oriented fashion and should be encoded as ASCII.  Carriage Return (ASCII 13) and/or Line Feed (ASCII 10) both indicate a new line (so the format is agnostic to Unix or DOS-style line endings).

It is recommended that the filename end in .dfg or .gdef.

### 1.1 Comments

All lines leading with a Semicolon (ASCII 59) or Hash (ASCII 35) are not processed by the parser.  These can be used to communicate information to Humans, Software, or Robots reading the file, but should be ignored by the configuration interface.

    ; This is a comment
    ; It will be ignored by the parser
    # This is also a comment
        ; Comments can be indented, too!

Comments are not allowed at the end of a line containing other content.

### 1.2 Directives

A directive is a special identifier following a leading Colon (ASCII 58).  These are used to indicate information about the lines to follow.  The lines between related directives form a block.  Most directive blocks are closed by the "end" directive (nesting is allowed in some cases), but there are a few special cases where the directive is only a single line and implicitly ended immediately.

### 1.3 Leading Whitespace

Leading whitespace is ignored on all lines.  This allows authors to use whatever style suits their needs; however, definitions should be formatted to enhance readability for Human readers.

See [guidelines.md](guidelines.md) for recommended guidelines.

### 1.4 Requirements, Constraints, and Features

For each element, tags may be listed in bold at the top of the section:

* Follows - This element must appear after all of the given elements listed here when used in the same block.
* Parent - This element must be a child of one of the following directives listed here; "Top" means it can be a top-level element of the file.
* Mandatory - This element must appear at least once within the block.
* Multiple - One or more elements may appear in the same block.
* Parameters - This block has parameter elements, which are documented in a related section.

Unless otherwise specified, all elements are unique within the block (cannot be defined twice).

### 1.5 Identifier Naming

An identifier is a symbolic name for the element.  It must only include one or more characters of the set {a-z,A-Z,0-9,_}, no whitespace is allowed

### 1.6 Menu Paths

Menu paths use a list of identifiers separated by "/".  A leading "/" indicates the top-level or "root" of the menu tree.

Absolute paths start with a "/", and override normal menu location determination.

Relative paths start with an identifier and are appended to the normal menu determination.

### 1.7 Parameter Elements

Within some entries there may be parameters (one on each line) of the form:

    [whitespace]parameter value[whitespace]

Note that trailing whitespace is ignored.

## 2 Configuration Option Structure

The configuration options available to the user are intended to be categorized and presented as a menu.  The menus themselves are not selectable options, merely conceptual groupings and sub-groupings of sets of options.

### 2.1 Configuration Entry

**Parent**={Top,menu} **Multiple** **Parameters**

Each user-configurable option must be defined with the "config" directive up until the matching "end" directive.  The config directive requires an identifier name afterward.

Example:

    :config MYMODULE_ENABLED
        type BOOL
        title "Enabled"
    :end

#### 2.1.1 Type Parameter

**Parent**=config **Mandatory**

This defines the acceptable type the user may set the value (and implicitly, also the range when applicable).  Acceptable values are:

* BOOL - A logical expression, which is either TRUE or FALSE
* FLOAT - A "native" floating point number.
* INT - A "native" signed integral number.
* STRING - A text array.  Bounding by double quotes (ASCII 34) is recommended.

NOTE: In this context, the acceptable range of "native" values is determined by the python interpreter AND the compiler.

#### 2.1.2 Title Parameter

**Parent**=config

This sets a short title for the parameter, which will be used as the menu item text in the configuration interface.

If omitted, the name of the config is used instead.

#### 2.1.3 Default Parameter

**Parent**=config **Follows**=type

This defines the value presented to the user for selection. when no value is given.  If omitted and not set by the user, the setting is considered "not defined" in the output.

The range of acceptable values are determined by the type parameter.

#### 2.1.4 Description Parameter

**Parent**=config

This is a longer, more verbose description of the setting when more detail than the title is needed to explain.

#### 2.1.5 Menu Parameter

**Parent**=config

This defines the menu path to use for this setting.

Use of this parameter directly should be uncommon; favoring "menu" directives instead.  See [guidelines.md](guidelines.md) for recommended guidelines.

### 2.2 Quick Configuration Entries

Simple configuration entries may be shortened to one line with one of the following directives.

* config_b - A BOOL parameter
* config_f - A FLOAT parameter
* config_i - An INT parameter
* config_s - A STRING parameter

These are short for a basic minimal config element of the given type:

    :config_b MYMODULE_FOO_SUPPORT

Is equivalent to:

    :config MYMODULE_FOO_SUPPORT
        type BOOL
    :end

### 2.3 Menu Block

**Parent**={Top,menu,config} **Multiple** **Parameters**

This block defines the directory path for nested elements until the matching "end" directive.  The menu directive requires a descriptive title afterward.

It is recommended to use menus for grouping options for modules/packages and their sub-components and/or feature groups.  See [guidelines.md](guidelines.md) for more information.

Example:

    :menu My Module
        description "Contains configuration settings for my module."
        :config MYMODULE_ENABLED
            type BOOL
            title "Enabled"
        :end
        :menu Feature 1
            config_s MYMODULE_FEATURE1_TEXT
        :end
    :end

In the above example, the menu structure will produce:

* Path "/" contains:
  * My Module (sub-menu)
* Path "/My Module" contains:
  * Enabled (BOOL value)
  * Feature 1 (sub-menu)
* Path "/My Module/Feature 1" contains:
  * MYMODULE_FEATURE1_TEXT (STRING value)

#### 2.3.1 Description Parameter

**Parent**=menu

This is a longer, more verbose description of the settings within this folder when more detail than the title is needed to explain.
