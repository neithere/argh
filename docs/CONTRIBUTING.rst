Contributing to Argh
====================

Argh would not be so good without the FOSS community.

Your contributions matter!

This document describes how to contribute to Argh.

Issues, Bug reports, Feature requests
-------------------------------------

If you have a question, a bug report or a feature request, please
`create an issue <https://github.com/neithere/argh/issues/new/choose>`_.

Please include, if possible:

* a minimal reproducible example;
* a description of the expected and observed behaviour;
* a description of your environment (OS, Python version, etc.).

Code changes
------------

Starting work on a new release
..............................

* Assign tasks to the release milestone.
* Create a release branch (e.g. `release/v0.30.4`) from `master`.
* Bump version in `pyproject.toml`.
* Create section in `CHANGES.rst` for the new version.
* Create a pull request from the release branch to `master`.

Contributing to the release
...........................

* Create a feature branch from the release branch.
* Make changes, commit, push, create a pull request (target branch = release).
* Make sure the pipeline is green.
* Ask for review.
* Merge the pull request.

  * Default strategy: squash.  Fast-forward or rebase if:

    - there are multiple commits from different authors;
    - there are commits which are important to keep separate.

Finalising the release
......................

* Make sure the pipeline is green.
* Make sure all tasks in the release milestone are "ready for release".
* Update `CHANGES.rst`, then proof-read on RTD:

  * make sure all merged PRs are mentioned;
  * add current date in section title.

* Create a GitHub release: https://github.com/neithere/argh/releases/new

  * based on the release branch;
  * new tag in the format `v0.30.4`;
  * tick "Set as the latest release" checkbox;
  * click the "Generate release notes" button;
  * add link to RTD changelog.

* Monitor the release pipeline: https://github.com/neithere/argh/actions

  * if it failed, fix and re-create the release with the same tag.

* Merge the release branch into `master`.

  * don't squash!
