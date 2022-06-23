# Backup of `dev/` folder

## Background

For many years, the Spinal Cord Toolbox repository has contained a `dev/` folder with the following purpose:

> This is the location for scripts that are used in development, but are not part of the core `spinalcordtoolbox` package. Some examples: 
>
> * Utility scripts to automate menial tasks
> * Scripts used to train machine learning models
> * Scripts used to generate templates/atlases
> * Scripts used to build pre-compiled binaries used by SCT.

However, these files are rarely returned to after they've been used, and storing these files in the Spinal Cord Toolbox repository unnecessarily bloats the size of the project's source code. For these reasons,  there have been several efforts by SCT's developers to clean up the `dev/` folder:

* **May 5, 2016**: A commit (https://github.com/spinalcordtoolbox/spinalcordtoolbox/commit/1dd49e5ec16aaf665485f3a04ace145a443b580d) is added to the `release` branch that removes [_the entire `dev/` folder_](https://github.com/spinalcordtoolbox/spinalcordtoolbox/tree/1dd49e5ec16aaf665485f3a04ace145a443b580d) (1600+ files) from the release branch.
* **March 4, 2018**: PR [#1631](https://github.com/spinalcordtoolbox/spinalcordtoolbox/pull/1631) is merged to `master` (https://github.com/spinalcordtoolbox/spinalcordtoolbox/commit/0590a7c38cfb31e59d5478c2ad941558a80590fb) and removes a subset of the `dev/` folder from `master` (1000+ files). 

Despite these cleanup efforts, the `dev/` folder still complicated SCT's release procedures.

## Repo description

This repository is part of a third cleanup effort that involves the following steps:

* Cloning the SCT repo to preserve the history of changes to the `dev/` folder.
* Deleting everything but the `dev/` folder, so that the clone can act as a backup for the `dev/` folder.
* Deleting the `dev/` folder from the SCT repo.

## Using this repo

If there is a specific `dev/` file that you're looking for that's not present on `master`, please check out any of the following commits, as they may contain the file you're looking for:

* 265541ec2b1daf121e7a8eb64efd5b764902790c: The commit immediately before the 2016 cleanup of the `dev/` folder (on the `release` branch).
* 035336b959802f0bb23a3d0b714e674ce5a01e6a: The commit immediately before the 2018 cleanup of the `dev/` folder (on the `master` branch).

