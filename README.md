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

By default the script searches for maven projects in a current directory. The directory can be changed using *-r* parameter (e.g. -r /home/username/path/to/project)

You can pass maven arguments to the script, using --maven="" arg, (e.g. --maven="-fae -DskipTests")
