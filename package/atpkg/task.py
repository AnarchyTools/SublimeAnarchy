from .error import PackageError
from .overlay import Overlay

class Task(object):

	@staticmethod
	def factory(data, where):
		if not isinstance(data, dict):
			raise PackageError("Task must be a dictionary")
		tool = data.get("tool", None)
		if not tool:
			raise PackageError("You have to define a tool")
		if tool == "atllbuild":
			return LLBuildTask(data, where)
		elif tool == "shell":
			return ShellTask(data, where)
		elif tool == "xctestrun":
			return XCTestTask(data, where)
		elif tool == "nop":
			return NOPTask(data, where)
		else:
			return UnknownTask(data, where)

	def __init__(self, task, where):
		if not isinstance(task, dict):
			raise PackageError("Task must be a dictionary")
		self.dependencies      = task.get("dependencies", [])
		self.tool              = task.get("tool", None)
		self.overlays          = {}
		for (name, data) in task.get("overlays", {}).items():
			self.overlays[name] = Overlay(data)
		self.used_overlays     = task.get("use-overlay", [])
		self.required_overlays = task.get("required-overlays")
		self.root_path 		   = where
		super().__init__()


class LLBuildTask(Task):

	def __init__(self, task, where):
		super().__init__(task, where)
		self.name                      = task.get("name", None)

		self.output_type               = task.get("output-type", None)
		self.sources                   = task.get("sources", [])
		self.publish_product           = True if task.get("publish-product", "false") == "true" else False
	
		self.bootstrap_only            = True if task.get("bootstrap-only", "false") == "true" else False
		self.llbuild_yaml              = task.get("llbuild-yaml", "llbuild.yaml")

		self.compile_options           = task.get("compile-options", [])
		self.link_options              = task.get("link-options", [])
		self.link_sdk                  = True if task.get("link-sdk", "true") == "true" else False
		self.whole_module_optimization = True if task.get("whole-module-optimization", "false") == "true" else False

		self.link_with                 = task.get("link-with", [])
		self.swiftc_path               = task.get("swiftc-path", None)

		self.include_with_user         = task.get("include-with-user", [])

		self.xctestify                 = True if task.get("xctestify", "false") == "true" else False
		self.xctest_strict             = True if task.get("xctest-strict", "false") == "true" else False

		self.umbrella_header           = task.get("umbrella-header", None)
		self.module_map                = task.get("module-map", None)


		self.source_files              = self.collect_sources()

		if not self.name:
			raise PackageError("A llbuild task needs a (module-)name")

	def collect_sources(self):
		# see collectSources in the real atpkg
		collectedSources = []
		import os, fnmatch, glob
		absRoot = os.path.dirname(self.root_path)
		for descriptor in self.sources:
			if descriptor.endswith("**.swift"):
				full_descriptor = os.path.join(absRoot, descriptor)
				for root, dirs, files in os.walk(os.path.dirname(full_descriptor)):
					collectedSources.extend([os.path.join(root, f) for f in fnmatch.filter(files, "*.swift")])
			else:
				full_descriptor = os.path.join(absRoot, descriptor)
				collectedSources.extend(glob.glob(full_descriptor))

		# convert back from abspaths
		collectedSources = [os.path.relpath(x, start=absRoot) for x in collectedSources]
		return collectedSources

class ShellTask(Task):

	def __init__(self, task, where):
		super().__init__(task, where)
		self.script = task.get("script", None)
		if not self.script:
			raise PackageError("Shell task needs a script")


class XCTestTask(Task):

	def __init__(self, task, where):
		super().__init__(task, where)
		self.test_executable = task.get("test-executable", None)
		if not self.test_executable:
			raise PackageError("XCTest task needs an executable")


class NOPTask(Task):

	def __init__(self, task, where):
		super().__init__(task, where)

class UnknownTask(Task):

	def __init__(self, task, where):
		super().__init__(task, where)


