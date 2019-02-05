# Guidelines

This document contains guidelines recommended by the Author and/or maintainers of Globifest.  These guidelines are mostly personal opinions and shall not be construed as mandatory practices, except to the extent required by important external entities (such as your company, boss, or project leadership).

In case of disagreement of, conflict with, or personal disdain of these guidelines, please disregard this document and direct all animosity to /dev/null.  Constructive suggestions are welcome through normal software contribution methods.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1. Usage Considerations

This section contains important things to consider when constructing Globifest files.

### 1.1 Always use Relative Paths

Your files may move in the future.  Using relative paths not only improves readability of the file, but also improves the portability of your module.

### 1.2 Separate Shareable Code from Application Targets

To facilitate usage of shareable code in other target applications, you should break up the shareable parts of the code from the parts which are only applicable to a specific build target (i.e., the executable image).

* A shared component should include a Manifest and a Definition
* The top-level application/target should include a Project and Config file(s)

See samples/HelloWorld for example.  Note that the App code is not in the top-level directory, but instead as a separate component.  Defining application-specific code as its own component will make it easier to generate multiple applications from the same folder.

### 1.3 Considerations for Shared Code

When writing code that is meant to be shared for use in externally-defined applications, it is important to:

* Avoid external dependencies:
    * Folder structure (i.e., the name of the folder where someone has extracted your code into)
    * Package names, etc...
* Use (hopefully) unique names:
    * Group definition items into a single top-level menu named after your module
    * Use prefixes on identifiers which are unique to your module (ex: an identifier used for the `FooBaz` module might be `FOOBAZ_ENABLE_BAR`).
* Avoid ".." in relative paths, especially at the top-level directory of your module.

### 1.4 Considerations for Top-Level Applications

* Use one project file for each link-able build target (this improves portability with waf and other tools).
* Use configuration layering for projects where the long-term goal is to generate multiple variants of a product, even if there is only one variant of some layers.
    * Having separate layers enables these configurations to be shared between multiple project files easily.
* Define a "common" or "base" layer.  At some point you'll probably want to set global options that are independent of any variant-specific layer; and this will make it easier to avoid duplication of settings.
* Separate application-specific code into its own component, to make it easier to extend the project for other build targets (unit test suite, an auxiliary tool, etc...).

### 1.5 Indentation

Leading spaces are ignored in the files, but it is still recommended to indent blocks inside the beginning and end directives.

* Four (4) spaces are preferred for Globifest files (this aligns visually with some directive names).
* Tabs may be used if you REALLY want to...
* Whatever you use, be CONSISTENT within ALL files in your source code.

### 1.6 Expression Spacing

* Spaces are recommended around binary operators (ex: `a == b`)
* Considering that parentheses are only used in conditional expressions, it is LOOSELY recommended to avoid spacing in-between the contents.  Ex: `(a == b) || (c && d)`

## 2 Config Files

To create a new config file, there are two recommended methods:

* From a Linux-based shell: `touch ./my_config.gconf`
* From a CMD shell: `echo. > ./my_config.gconf`
* GUI: Open your favorite text editor to a new blank document.  Save the file.

**DO NOT HAND-EDIT CONFIG FILES!**

The `config` tool does a lot of cool things to help you set up the configuration appropriately:

* Validation of the input data
* Limits you to allowed choices for certain configs (ex: bool values)
* Ensures values are written correctly
* Shows you where a value is defined in the selected variant of all layers (useful to see where something is defined and where you might be overriding the value).
* Shows you all the options, even if they are not defined.

## 3 Manifest Files

### 3.1 Quick Start for Existing Files

One way to get a base manifest file for an existing repository is to pipe the output of a shell command to a file.

Examples for bash:

    ls -1 *.cpp > manifest.mfg
    find . | grep -e "\.cpp" > manifest.gman

Example for cmd:

    dir /b *.cpp > manifest.gman

Then you can open the file and edit it to how you prefer.  Note that the examples above are very simplistic; you can use globbing to find all files based on a pattern.

### 3.2 Organize Source files by Folder

One way to make it easier to maintain your project is to organize source files by folder according to what features are enabled or disabled:

    :source
		:if(FOO_ENABLE_BAR)
			bar/*.c
		:end

		:if(FOO_ENABLE_BAZ)
			baz/*.c
		:end

A few notable benefits to this include:

* Easily determine what files are built per-feature based on the path.
* Allows use of a single glob expression to include all source files in the directory; so new files are automatically included.
* Helps break up large code bases into manageable parts.

### 4 Project Files

See the earlier section "Considerations for Top-Level Applications" as well.

The project will auto-detect file names for the configuration files if they are placed in the same directory as the project file as `<variant>_<layer>.cfg`.  If there are a lot of layers and variants, it is recommended to break this up into folders.  Ex: A layer named "os" might have `prefix=config/os/`.

If you have multiple applications, it is recommended to make an application configuration layer with the variant being different per-project.  You could also put all variants into all projects to allow editing the settings for each app layer from any file, but this may break down if different build targets do not all have the same layering structure.

You can change the filename with `suffix` for default-program association compatibility or applying special line-ending rules for software version control tools like git.  This might be necessary if editing project settings in the same repository on different operating systems.

### 5. Definition Files

See the earlier section "Considerations for Shared Code" as well.

It is recommended to treat application code as a sub-component, so it should have a uniquely named menu as well (ex: `MyTool/App Name` for `MYTOOL_APP_NAME`, and `UnitTests/Build All` for `UNITTESTS_BUILD_ALL`).

For code which is shared between multiple top-level applications, you can treat it as a shared component even if it is not shared with any other projects.  This allows each application to use the same .gdef file, but store the settings in their own app configuration layer variant.

For example: you might have some common app code which relies on the application name.  In that case you could define it under the identifier `APP_TITLE`.
