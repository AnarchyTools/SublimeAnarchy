import os
from .atpkg.atpkg_package import Package
from .atpkg.task import LLBuildTask

def findAtpkg(forSourceFile):
    """Finds an atpkg by walking up the filesystem"""
    forSourcefile = os.path.abspath(forSourceFile)
    dirname = os.path.dirname(forSourceFile)
    while dirname != "/":
        trial = os.path.join(dirname, "build.atpkg")
        if os.path.exists(trial):
            return trial
        dirname = os.path.dirname(dirname)

def taskForSourceFile(sourcePath):
    """Looks up an LLBuildTask for the given source path"""
    atpkg = findAtpkg(sourcePath)
    return Package.fromFile(atpkg).task_for_file(sourcePath)

def otherSourceFilesAbs(sourceFile):
    """Finds the other source files (absolute paths) for the given path, based on looking up the atpkg build file"""
    task = taskForSourceFile(sourceFile)
    if not task:
        print("Warning: not able to look up atpkg for file %s" % sourceFile)
        return []
    sourcePath = os.path.relpath(sourceFile, start=os.path.dirname(task.root_path))
    otherSources = filter(lambda x: x != sourcePath, task.source_files)
    otherSources = map(lambda x: os.path.abspath(os.path.join(os.path.dirname(task.root_path), x)), otherSources)
    return list(otherSources)

