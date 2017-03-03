# IncreMaven
IncreMaven analyzes your changes and launches maven rebuild only for the really changed projects. Changes analysis can be based on your local changes or incoming changes from the repository.

Local changes build is useful, when you have to modify code for dependent modules. Just run the script and it will build, what was changed and _not yet_ built.

Building the incoming changes is useful on the build servers. Usually developers commit changes only for a couple of modules and rebuilding only them is safe enough and can save a lot of building time and resources.

_Changes gathering is based on version control changes, but does extended analysis based on plan file changes_

## Requirements
* Linux / Windows
* Python (2 or 3)
* Maven (3+)
* svn (1.6+)

## How to use
1. Download _rebuild.py_ (local build) or _ci_rebuild.py_ (for build server) file from [Latest releases](https://github.com/bugy/incremaven/releases/latest)
2. Specify the list of the parameters, if needed (see below)
3. Run the script and see the results :)
4. Rerun the script each time you want to have up-to-date artifacts

### Parameters
* -r (--root_path) - the path to the project. By default, if argument is missing, the script will run in current directory
* -m (--maven) - pass additional arguments to maven execution. E.g. --maven="-fae -DskipTests"
* -o (--root_only) - a flag (no value needed), making the script to build only the child projects, which are submodules (direct or nested) of the root project.
* -t (--track_unversioned) - a flag (no value needed) for considering unversioned files in local changes analysis

### Some tips
* Pass -fae (fail at end) parameter to maven
* Setup the script as a run configuration in your favourite IDE 
* Use the script, even if you are currently working on a single module
* Use -amd (also make dependants) for ci_rebuild

## Additional features
* Build a project even if it's not a child module of the root project (maven doesn't allow it by default)
* Don't allow maven to replace your built artifacts in your local repository from remote repository
* Rebuild reverted project, if it was already built with some modifications
* Quite build mode for local rebuilding (no tons of maven logs)

## How it works 
The functionality of the script is based on the maven feature to build only specified projects (with -pl parameter). And the main work of the script is to prepare such list in the best way and build only really needed modules.

Main script command is '_mvn clean install -pl [prepared_list]_', but it can be extended based on user options or some internal optimizations. 

### Local changes analysis
The starting point for IncreMaven is your uncommitted changes in SVN:

1. For every local svn change, the corresponding project is found
2. For every changed project (from step 1) it is checked, whether it was modified after the last build
  * If the project modification is newer, then the project will be built
  * Otherwise it will be skipped (almost, see features for details).

### Incoming changes analysis
At the first launch, IncreMaven builds the whole project and saves current revision information.
On all the subsequent calls, the script checks svn for the differences between the current revision and the last built one. Then it rebuilds the projects, corresponding to these changes. 

If the build failing, then current revision is not saved and next rebuild will try to rebuild these changes again.

In most cases it's better to supply -amd (also make dependants) flag to maven, to make sure, that the changes didn't break any child projects. 
