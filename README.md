# confluencer

A CLI tool to automate common Confluence maintenance tasks and content publishing.

 [![Travis CI](https://api.travis-ci.org/1and1/confluencer.svg)](https://travis-ci.org/1and1/confluencer)
 [![Coveralls](https://img.shields.io/coveralls/1and1/confluencer.svg)](https://coveralls.io/r/1and1/confluencer)
 [![GitHub Issues](https://img.shields.io/github/issues/1and1/confluencer.svg)](https://github.com/1and1/confluencer/issues)
 [![License](https://img.shields.io/pypi/l/confluencer.svg)](https://github.com/1and1/confluencer/blob/master/LICENSE)
 [![Latest Version](https://img.shields.io/pypi/v/confluencer.svg)](https://pypi.python.org/pypi/confluencer/)
 [![Downloads](https://img.shields.io/pypi/dw/confluencer.svg)](https://pypi.python.org/pypi/confluencer/)


## Overview

The ``confluencer`` command line tool (or ``cfr`` for short) allows you to
control your Confluence installation from a shell prompt, and thus automate
(mass) content changes and reports.

For example, ``cfr tidy`` applies rules to remove artifacts from a page's body
left behind if you cut&copy content from other sources (especially *FosWiki* pages).

The ``confluencer.api`` Python package can be used in your own scripts to implement
more complex custom use-cases that are not covered by the provided commands.
It provides helpers like converting an URL as found in the web interface (i.e.
your browser's location bar) into an API one, and abstractions for typical
*Confluence* objects like pages and spaces.


## Installation

*Confluencer* can be installed via ``pip install confluencer`` as usual,
see [releases](https://github.com/1and1/confluencer/releases) for an overview of available versions.
To get a bleeding-edge version from source, use these commands:

```sh
repo="1and1/confluencer"
pip install -r "https://raw.githubusercontent.com/$repo/master/requirements.txt"
pip install -UI -e "git+https://github.com/$repo.git#egg=${repo#*/}"
```

See [Contributing](#contributing) on how to create a full development environment.

To add bash completion, read the [Click docs](http://click.pocoo.org/4/bashcomplete/#activation) about it,
or just follow these instructions:

```sh
cmdname=confluencer
mkdir -p ~/.bash_completion.d
( export _$(tr a-z- A-Z_ <<<"$cmdname")_COMPLETE=source ; \
  $cmdname >~/.bash_completion.d/$cmdname.sh )
grep /.bash_completion.d/$cmdname.sh ~/.bash_completion >/dev/null \
    || echo >>~/.bash_completion ". ~/.bash_completion.d/$cmdname.sh"
. "/etc/bash_completion"
```


## Usage

See the [main documentation](http://confluencer.readthedocs.io/) at *Read the Docs*.


## Contributing

Contributing to this project is easy, and reporting an issue or
adding to the documentation also improves things for every user.
You don’t need to be a developer to contribute.
See [CONTRIBUTING](https://github.com/1and1/confluencer/blob/master/CONTRIBUTING.md) for more.

As a documentation author or developer,
to create a working directory for this project,
call these commands:

```sh
git clone "https://github.com/1and1/confluencer.git"
cd "confluencer"
. .env --yes --develop
invoke build --docs test check
```

You might also need to follow some
[setup procedures](https://py-generic-project.readthedocs.io/en/latest/installing.html#quick-setup)
to make the necessary basic commands available on *Linux*, *Mac OS X*, and *Windows*.


## References

**Tools**

* [Cookiecutter](http://cookiecutter.readthedocs.io/en/latest/)
* [PyInvoke](http://www.pyinvoke.org/)
* [pytest](http://pytest.org/latest/contents.html)
* [tox](https://tox.readthedocs.io/en/latest/)
* [Pylint](http://docs.pylint.org/)
* [twine](https://github.com/pypa/twine#twine)
* [bpython](http://docs.bpython-interpreter.org/)
* [yolk3k](https://github.com/myint/yolk#yolk)

**Packages**

* [Rituals](https://jhermann.github.io/rituals)
* [Click](http://click.pocoo.org/)


## Related Projects

* [Conflence.py](https://github.com/RaymiiOrg/confluence-python-cli) – A 1:1 mapping of the REST API to a command line tool.
* [PythonConfluenceAPI](https://github.com/pushrodtechnology/PythonConfluenceAPI) - A Pythonic API wrapper over the Confluence REST API.
* [rst2confluence](https://github.com/netresearch/rst2confluence) – Convert reStructuredText to Confluence style wiki markup.


## Acknowledgements

…
