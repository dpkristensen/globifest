<!-- markdownlint-disable MD025 MD026 -->

# Globbing Package Manifest Builder

This tool lets you describe package manifests in a way that is abstract to whatever build and configuration system you use.

# Legal Stuff

Please read the Software License ([LICENSE.md](LICENSE.md)) and Contributor License Agreement ([CLA.md](CLA.md)).

# FAQ

## What does globifest mean?

The name "globifest" is a portmanteau of "globbing" and "manifest".

## Why is ANOTHER package manifest tool needed???

My primary motivations for this are:

1. Package manifests are usually not portable.  They're tied to a specific build system, and also a configuration system, which may also not be portable.  Ex: Make + Kconfig for Linux, but it is harder to use this on Windows
2. I wanted a package manifest + configuration system which had little to no dependencies.  Python is a natural fit because I also like to use waf as a build system, and it is fairly ubiquitous and stable.
3. I want the output from the manifest to be easy to import into other build systems.
4. I want to help others benefit from this system.

## How can I use this in my build system?

Some build system integration is already planned:

* waf
* Make
* CMake
* Visual Studio?

### Importing as a Python module

Import the "globifest" module in the root directory, or install it to your system library.

### Building deliverables via the command line

Run the ./build python script on each manifest to generate output.
