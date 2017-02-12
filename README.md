# rebuilder
This is a python project for assisting in easy project building.

*Currently only java + mvn + svn + linux/win are supported*

The project analyzes changed files (svn + modification date) and rebuilds maven artifact,
if it's outdated.

## Requirements
* Linux / Windows
* Python (2 or 3)
* Maven (3+)
* svn (1.6+)

## Usage
There are 3 ways of using the script:

1. Download and use [rebuild.py](https://github.com/bugy/rebuilder/releases/download/1.1.0/rebuild.py). It's a single and minified script, based on the sources of the repository
2. Checkout the project and simply run *build.py* (instead of #1)
3. IntellijIDEA users can copy run config (*idea-rebuilder.xml*) to .idea/runConfigurations and specify path to *rebuild.py* (from #1)

Arguments:
* -r (--root_path) - the path to the project. By default, if argument is missing, the script will run in current directory
* -m (--maven) - pass additional arguments to maven execution. E.g. --maven="-fae -DskipTests"
* -o (--root_only) - a flag (no value needed), making the script to build only the child projects, which are submodules (direct or nested) of the root project.
