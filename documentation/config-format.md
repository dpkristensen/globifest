# Globifest - Configuration

Configuration files store the selected options to use when building your project.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 Configuration Scope

The scope of a configuration file is ONE variant of ONE layer (see project-format.md).

### 2 General Format

Config files are parsed in a mostly line-oriented fashion and should be encoded as ASCII.  Carriage Return (ASCII 13) and/or Line Feed (ASCII 10) both indicate a new line (so the format is agnostic to Unix or DOS-style line endings).

It is recommended that the filename end in .cfg or .gconf.

NOTE: The provided application will generate and modify these files for users, but they can be created/modified manually or via a different application as well.

### 2.1 Comments

All lines leading with a Semicolon (ASCII 59) or Hash (ASCII 35) are not processed by the parser.  These can be used to communicate information to Humans, Software, or Robots reading the file, but should be ignored by most tools.

    ; This is a comment
    ; It will be ignored by the parser
    # This is also a comment
        ; Comments can be indented, too!

Comments are not allowed at the end of a line containing other content.

### 2.1.1 Comment Association

Comments in a contiguous block preceding a setting are associated with the setting, for the purposes of re-generating the file and display in the configuration interface.

When this occurs, the content of a comment is extracted and formatted for ease of use.  After the beginning of the comment, whitespace is stripped off of the remaining text to form the content.

    ;      Extra whitespace!!!

The content of the above comment is "Extra whitespace!!!".

### 2.1.2 Multi-line Comment Formatting

Multiple non-blank lines of comment content are combined together and separated by a space to form a paragraph.  However, lists can be created with one of the following:

* Asterisk (*)
* Plus sign (+)
* Minus sign (-)
* Hash symbol (#)

Example:

    ; To create a bulleted list,
    ; this is what needs to be typed:
    ;
    ; * Item 1
    ; * Item 2
    ;
    ; Notice the blank line between the
    ;     paragraph and the list.

This comment would have lines:

* Line 1 = "To create a bulleted list, this is what needs to be typed:"
* Line 2 = ""
* Line 3 = "* Item 1"
* Line 4 = "* Item 2"
* Line 5 = ""
* Line 6 = "Notice the blank line between the paragraph and the list."

### 2.2 Stored Settings

Settings are stored one on each line as a simple key/value pair with whitespace ignored:

    [whitespace]identifier=value[whitespace]

The identifier corresponds to the definition file, and the value is user-supplied.

Example:

    MYMODULE_ENABLED=TRUE
    MYMODULE_FEATURE1_TEXT=This is a cool feature!

The acceptable input for value is dependent upon the input type.