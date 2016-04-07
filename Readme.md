# Sublime Text 3 plugin for developing with the Open Source Version of Swift

This plugin is specifically designed to work with the [Anarchy Tools](http://anarchytools.org) build system and package manager.

## Features

- Swift 3 Syntax highlighting
- `build.atpkg` Syntax hilighting
- Building with `atbuild`
- Highlighting build errors in the source files
- Build log (terminal output) in an output panel in Sublime with output coloring and clickable file names

Some features currently only work on OSX:

- SourceKit autocompletion
- SourceKit documentation fetching (kind of buggy, blame SourceKit)

## Roadmap

- Add debugger support
    - Setting breakpoints
    - Running with connected stdin/out/err in output panel
    - lldb debug prompt
    - local variable display
- SourceKit as you type error display
- Package manager support
- Showing just an interface of a Swift file without implementation
- Jump to definition
- Find callers

## Setup

Use the default Sublime method of overriding configuration from the menu.
Available configuration options:

- `sourcekit_path` path to `sourcekitd` (default: `/Library/Developer/Toolchains/swift-latest.xctoolchain/usr/lib/sourcekitd.framework/sourcekitd`)
- `sourcekit_sdk` path to the sdk SourceKit shall use (default: `/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.11.sdk`)
- `lldb_executable_path` path to lldb binary to use for the debugger
- `atbuild_path` path to the `atbuild` binary from Anarchy Tools (default: `/usr/local/bin/atbuild`)
- `atpm_path` path to the `atpm` binary from Anarchy Tools (default: `/usr/local/bin/atpm`)

## How to use

The syntax highlighter should work out of the box (make sure you don't have another swift syntax hilighter installed), for the build process to work you'll need to open a Sublime project file.

Example content of `Project.sublime-project`:

```
{
	"folders":
	[
		{
			"path": ".",
			"folder_exclude_patterns": [ ".atllbuild", "bin" ],
		}
	]
}
```

Put that into your project root and use the menu entry `Project->Open Project...` to open the project (or double-click in your filesystem browser or even open with `subl <ProjectFile>` from the command line.)

If the project is open just use the Command Palette to execute some Anarchy Tools commands (all prefixed with "AnarchyTools:"). To speed up rebuilding the last target you built use the shortcut `CMD-SHIFT-A` (OSX) or `CTRL-SHIFT-A` (Linux) to re-execute the last chosen task.
