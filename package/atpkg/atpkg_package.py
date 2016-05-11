import os

from .task import Task, LLBuildTask
from .dependency import ExternalDependency
from .error import PackageError
from .overlay import Overlay

from ..clojure.lexer import ClojureLex
from ..clojure.parser import ClojureParse

lexer = ClojureLex().build()
parser = ClojureParse().build()

class Package(object):

	@staticmethod
	def fromFile(fileName):
		with open(fileName) as f:
			atpkgFile = f.read()
		return Package(atpkgFile, fileName)
	
	def __init__(self, data, root_path):
		ast = parser.parse(data, lexer=lexer)
		if not ast:
			raise PackageError("Empty clojure ast")
		if ast[0] != "package":
			raise PackageError("Not a valit atpkg package")

		self.name = "unknown"
		self.imports = []
		self.tasks = {}
		self.external_packages = []
		self.overlays = {}
		self.root_path = root_path

		for i in range(1, len(ast), 2):
			self.parse(ast[i], ast[i+1])

		super().__init__()

	def parse(self, key, value):
		if key == 'name':
			self.name = value
		elif key == 'import-packages':
			if not isinstance(value, list):
				raise PackageError("Package imports have to be a list")
			self.imports = value
		elif key == 'tasks':
			if not isinstance(value, dict):
				raise PackageError("Package tasks have to be a dictionary")
			for (name, task) in value.items():
				self.tasks[name] = Task.factory(task,self.root_path)
		elif key == 'external-packages':
			if not isinstance(value, list):
				raise PackageError("External packages have to be a list")
			for package in value:
				self.external_packages.append(ExternalDependency(package))
		elif key == "overlays":
			if not isinstance(value, dict):
				raise PackageError("Overlay definition has to be a dictionary")
			for (name, data) in value:
				self.overlays[name] = Overlay(data)
		else:
			print("Skipping unknown key {name}".format(name=key))

	def task_for_file(self, filename):
		sourcePath = os.path.relpath(filename, start=os.path.dirname(self.root_path))
		for task in self.tasks.values():
			if not isinstance(task, LLBuildTask): continue
			if sourcePath in task.source_files:
				return task
		return None
