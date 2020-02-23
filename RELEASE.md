1. Generate changelog: Run `loghub spyder-ide/spyder-unittest --milestone vx.y.z`
1. Edit changelog and commit
1. Bump version number in `spyder_unittest/__init__.py`
1. Remove non-versioned files: Run `git clean -xfdi`
1. Create source distribution: Run `python setup.py sdist` in root
1. Check that source distribution does not contain any unnecessary files (e.g., cache, `.pyc`)
1. Create wheel: Run `python setup.py bdist_wheel`
1. Test wheel: Uninstall current plugin and run `pip install dist/spyder_unittest-xxx.whl`
1. Check that `dist/` contains only the source distribution and wheel that you want to upload
1. Upload to PyPI: Run `twine upload dist/*`
1. Test: Uninstall current plugin and run `pip install spyder-unittest`
1. Commit `spyder_unittest/__init__.py`
1. Create a version tag on above commit: Run `git tag -a vx.y.z`
1. Change version number in `spyder_unittest/__init__.py` to `....dev0` and commit and push
1. If building conda package:
    1. Wait for bot to submit PR **or** edit `meta.yaml` in fork of `spyder-unittest-feedstock`, changing version number and hash computed with `sha256sum dist/spyder_unittest-x.y.z.tar.gz`, test with `conda build conda.recipe`, and submit PR
    1. When automatic tests on PR finish successfully, merge PR
    1. Wait for CI to build Conda package
    1. Copy: `anaconda copy conda-forge/spyder-unittest/x.y.z --to-owner spyder-ide`
    1. Test Conda package: Uninstall current plugin and run `conda install -c spuder-ide spyder-unittest`
1. Push commits and version tag  to `spyder-ide` repo: Run `git push remote_name vx.y.z`
1. Use GitHub to edit tag and publish release
1. Announce release on Google Groups
