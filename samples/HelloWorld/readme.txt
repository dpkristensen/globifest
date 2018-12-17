HelloWorld is a sample project illustrating package structure, and facilitates testing of parsers in a real-world environment.

To demonstrate parsing and see the output, run the build command from the top-level folder:

./build -i samples/HelloWorld/HelloWorld.gproj -o _Output/HelloWorld backend=windows

Note that the backend layer variant is specified; the common layer is not necessary to specify since it only has one variant.  So the following is equivalent:

./build -i samples/HelloWorld/HelloWorld.gproj -o _Output/HelloWorld backend=windows common=default

These files only exist to illustrate usage of the Globifest project packaging system, and may not build for actual compilers.
