# `python-cicd`

`python-cicd` is  a fully-featured Jenkins CI/CD pipeline for Python packages, including testing, building, and publishing to a PyPI repo as well as GitHub releases. It can notify you on IFTTT when it is done.

## Requirements

Your Python project must use `poetry`. It can optionally use `poethepoet` to define the tasks `test`, `build`, and `release-gh`, which should run tests, build a wheel, and release to GitHub, respectively.

You should have [jenkins-notification-library](https://github.com/zmarffy/jenkins-notification-library) as a shared library accessible by this job.

## Notes

* This can only build pure Python packages, as it uses poetry
* If your project requries extras to build, you can make a `cicd/Dockerfile.build` file in your Python repo with the requirements
