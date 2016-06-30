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
    if not atpkg: return None
    return Package.fromFile(atpkg).task_for_file(sourcePath)

def absPathArgParser(arr, task):
    """Looks at compile args and tries to replace paths with absolute ones"""
    fixedArr = []
    fix = False
    for i in arr:
        if fix:
            fix = False
            i = os.path.abspath(os.path.join(os.path.dirname(task.root_path), i))
        if i == "-I":
            fix = True
        fixedArr += [i]
    return fixedArr

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

