[![Latest Release](https://img.shields.io/badge/latest%20release-v1.0.0rc1-blue)](https://code.sankhyasutralabs.com/sslabs/cross-vertical/pre-post-libraries/dhvani/-/releases)

Introduction
-------------

This is a lightweight Python library for aeroacoustics and signal processing.
The primary usage is meant as an acoustics post-processing toolkit to go along with SankhyaSutra Labs' solver suite.
Functionality includes:

- Basic and advanced Fourier transform-based signal processing
- Ffowcs-Williams Hawkings (FWH) solvers for farfield aeroacoustics propagation. This includes solvers for:
  - Stationary sources and observers
  - Moving sources and observers
  - Quiescent or uniform free-stream flows



Installation
-------------

The package has been tested using the PDM backend tool, which allows the compilation and distribution of pure-Python and C-enhanced Python packages.
It is recommended that the package be built in a Python virtual environment to avoid clashes in installed packages.

To create and activate a Python virtual environment or `venv` in Python 3.4+, run the commands below.

```shell
$ python -m venv ~/.venv/<name_for_your_virtual_environment>
$ source <path_to_venv>/bin/activate
```

It is possible to install a new `venv` at any location on your system.
To change the location, simply modify the argument supplied in the first line of the code block above, and use this to `source` your `venv`.
To make it easier for re-use, you may consider adding an alias for the `source` command  in your `.bashrc`, `.bash_aliases` or `.bash_profile` file to be sourced whenver a new terminal is opened, like so:

```shell
alias my-pyenv="source <path_to_venv>/bin/activate"
```

To deactivate a `venv` that is currently loaded, simply type `deactivate` in the command line, like so:

```shell
$ deactivate
```

Once your `venv` is up and running, you can build the package by running the following command in the root directory of the project, where you can find the `pyproject.toml` and `requirements.txt` files.

```shell
$ python -m build
```

If the build goes as expected, you should see an output similar to the one shown below.

```
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
.
.
* Getting build dependencies for sdist...
* Building sdist...
.
.
.
* Building wheel from sdist
* Creating isolated environment: venv+pip...
* Installing packages in isolated environment:
.
.
* Getting build dependencies for wheel...
* Building wheel...
.
.
Successfully built dhvani-1.0.0rc1.tar.gz and dhvani-1.0.0rc1-py3-none-any.whl

```


This will build the distribution files for the package and place them in `<root folder>/dist`.
Within this folder, you should be able find two ways to distribute your package; the Python `wheel` file (with the `.whl` extension), and a compressed archive in the `.tar.gz` format.

To install the package on the target system, simply activate your `venv` and install the package using Python's built-in package manager `pip`.
The will install the package into the system's default `site-packages` folder.

```shell
python -m pip install dhvani-<version>-<python tag>-<abi tag>-<platform tag>.whl
```

The package needs to be compiled with Python 3.4+, but is ABI and platform-independent, i.e., it is compatible with all Python ABIs and can be installed on any platform (Unix/Windows).
Dhvani `wheel` files will thus always be in the format `dhvani-1.0.0rc1-py3-none-any.whl`.

To make a user-specific installation, you can still use `pip` with the `--user` command, which will install the package into the user's local `site-packages` instead of the system default.
This may be helpful in case a user wants to maintain more than one version of the package, to test or for any other conceivable reason.

```shell
python -m pip install dhvani-1.0.0rc1-py3-none-any.whl --user
```
