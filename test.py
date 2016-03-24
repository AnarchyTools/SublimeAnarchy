import sys


from atpkg.package import Package


for arg in sys.argv[1:]:
	with open(arg, "r") as fp:
		pkg = Package(fp.read())
		print(pkg.__dict__)
