# waf Integration

This document covers how to integrate globifest into the waf build system.

See <https://waf.io/> for more information on waf itself.

## 0 Legal Stuff

Please read the Software License ([LICENSE.md](../LICENSE.md)) and Contributor License Agreement ([CLA.md](../CLA.md)).

## 1 globitool

globitool is a tool that allows you to build Project files as a build target.  For this example, we'll assume the globifest repository is located at `/external/globifest`

### 1.1 Setting up wscript

#### 1.1.1 Configuration

First, make sure the tool is loaded in your `configure` step:

    def configure(conf):
        conf.load('globitool', tooldir='external/globifest/waf')

#### 1.1.2 Adding TaskGens

In your `build` step, use the GLOBITOOL function to parse the project file and dynamically create TaskGens that will build each file.

    def build(bld):
        # This project file only defines some sources, no link step is performed
        bld.GLOBITOOL(
            target="just_sources",
            project="just_sources.gproj",
            # When GLOBITOOL() creates a taskgen for the targets, these
            # parameters are passed as if calling bld() directly.
            tgt_params=dict(
                features="cxx"
                )
            # There is no link step, but an implicit stub target is created
            # to aggregate all of the targets produced with the target name
            # defined above.
            )

        # This project file builds a statically-linked library, which includes
        # the sources defined in the project as well as all the sources from
        # just_sources above.
        #
        # The output is either my_static_lib.lib or my_static_lib.a depending on
        # whether the target is for Windows or Posix.
        bld.GLOBITOOL(
            target="my_static_lib",
            project="my_static_lib.gproj",
            use="just_sources",
            tgt_params=dict(
                features="cxx"
                ),
            # When GLOBITOOL() creates a taskgen for the link step, these
            # parameters are passed as if calling bld() directly.
            # Again: the target name is used for this TaskGen.
            lnk_params=dict(
                features="cxx cxxstlib"
                )
            )

        # This project file builds an executable program, which builds any
        # sources defined in the project, as well as links against
        # my_static_lib.
        #
        # The output is either my_tool.exe or my_tool depending on
        # whether the target is for Windows or Posix.
        bld.GLOBITOOL(
            target="my_tool",
            project="my_tool.gproj",
            tgt_params=dict(
                features="cxx"
                ),
            # The only difference in the link step is usage of cxxprogram vs
            # cxxstlib.
            lnk_params=dict(
                features="cxx cxxprogram"
                )
            )

#### 1.1.3 Dependencies

Dependencies defined by the project files are handled within the variant's output directory.  This means you could end up with multiple copies of dependencies for each waf build variant.  One way around this would be to use a single build variant and parameterize the layer variant configuration.

#### 1.1.4 Generated Headers

Generators are run directly through the GLOBITOOl function, not as a separate build step.  This is to ensure the folders and header files exist for use in the TaskGens for each target that requires them.
