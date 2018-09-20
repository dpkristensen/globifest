# Guidelines

This document contains guidelines recommended by the Author and/or maintainers of Globifest.  These guidelines are mostly personal opinions and shall not be construed as mandatory practices, except to the extent required by important external entities (such as your company, boss, or project leadership).

In case of disagreement of, conflict with, or personal disdain of these guidelines, please disregard this document and direct all animosity to /dev/null.  Constructive suggestions are welcome through normal software contribution methods.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1. Usage Considerations

TODO: Random thoughts to write...:

* Always use relative paths
* Avoid creating multiple include paths when possible
* Module-unique naming conventions
* Spacing/alignment

## 2 Writing a Good Manifest

### 2.1 Quick Start for Existing Files

One way to get a base manifest file for an existing repository is to pipe the output of a shell command to a file.

Examples for bash:

    ls -1 *.cpp > manifest.mfg
    find . | grep -e "\.cpp" > manifest.mfg

Example for cmd:

    dir /b *.cpp > manifest.mfg

Then you can open the file and edit it to how you prefer.  Note that the examples above are very simplistic, and you can use the globbing functionality to replace this.

## 3 Writing a Good Config Definition

TODO
