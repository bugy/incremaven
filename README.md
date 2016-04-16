# rebuilder
This is a python project for assisting in easy project building.

*Currently only java+mvn+svn+linux are supported*

The project analyzes changed files (svn + modification date) and rebuilds maven artifact,
if it's outdated.

## Requirements
* Linux (for bash commands and paths)
* Python (2 or 3)
  * python-pathlib (pip install pathlib **or** apt-get install python-pathlib)
* Maven (3+)
* svn (1.6+)

## Usage
There are 3 ways of using the script:

1. Checkout scripts and simply run *build.py*
2. Use *assemble.py* to create a single script file and use it (instead of #1)
3. IntellijIDEA users can copy run config (*idea-rebuilder.xml*) to .idea/runConfigurations and specify path to *rebuild.py* (from #2)

By default the script searches for maven projects in a current directory. The directory can be changed using *-r* parameter (e.g. -r /home/username/path/to/project)

You can pass maven arguments to the script, using --maven="" arg, (e.g. --maven="-fae -DskipTests")

## Known issues
* *-test.jar changes are not checked
* assemble.py don't modify names, if the intersect
* only .java and pom.xml files are considered for the changes
* if as a result of file change, it becomes the same as in svn, then the file is not considered modified
