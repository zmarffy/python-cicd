# `python-cicd`

`python-cicd` is  a fully-featured Jenkins CI/CD pipeline for Python packages, including testing, building, and publishing to a PyPI repo as well as GitHub releases.

## Requirements

Your Python project must use `poetry`. It can optionally use `poethepoet` to define the tasks `test`, `build`, and `release-gh`, which should run tests, build a wheel, and release to GitHub, respectively.

## Notes

* This can only build pure Python packages
