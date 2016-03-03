..  documentation master file

    Copyright ©  2015 1&1 Group <git@1and1.com>

    ## LICENSE_SHORT ##
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


=============================================================================
Welcome to the “Confluencer” manual!
=============================================================================

.. image:: _static/img/logo.png

A CLI tool to automate common Confluence maintenance tasks and content publishing.

.. image:: https://img.shields.io/pypi/v/confluencer.svg#
   :alt: Latest Version
   :target: https://pypi.python.org/pypi/confluencer/

.. image:: https://api.travis-ci.org/1and1/confluencer.svg#
   :alt: Travis CI
   :target: https://travis-ci.org/1and1/confluencer

.. image:: https://img.shields.io/coveralls/1and1/confluencer.svg#
   :alt: Coveralls
   :target: https://coveralls.io/r/1and1/confluencer

.. image:: https://img.shields.io/github/issues/1and1/confluencer.svg#
   :alt: GitHub Issues
   :target: https://github.com/1and1/confluencer/issues


Installing
----------

*Confluencer* can be installed from PyPI
via ``pip install confluencer`` as usual,
see `releases <https://github.com/1and1/confluencer/releases>`_
on GitHub for an overview of available versions – the project uses
`semantic versioning <http://semver.org/>`_ and follows
`PEP 440 <https://www.python.org/dev/peps/pep-0440/>`_ conventions.

To get a bleeding-edge version from source, use these commands:

.. code-block:: shell

    repo="1and1/confluencer"
    pip install -r "https://raw.githubusercontent.com/$repo/master/requirements.txt"
    pip install -UI -e "git+https://github.com/$repo.git#egg=${repo#*/}"

See the following section on how to create a full development environment.

To add bash completion, read the
`Click docs <http://click.pocoo.org/4/bashcomplete/#activation>`_
about it, or just follow these instructions:

.. code-block:: shell

    cmdname=confluencer
    mkdir -p ~/.bash_completion.d
    ( export _$(tr a-z- A-Z_ <<<"$cmdname")_COMPLETE=source ; \
      $cmdname >~/.bash_completion.d/$cmdname.sh )
    grep /.bash_completion.d/$cmdname.sh ~/.bash_completion >/dev/null \
        || echo >>~/.bash_completion ". ~/.bash_completion.d/$cmdname.sh"
    . "/etc/bash_completion"


Contributing
------------

To create a working directory for this project, call these commands:

.. code-block:: shell

    git clone "https://github.com/1and1/confluencer.git"
    cd "confluencer"
    . .env --yes --develop
    invoke build --docs test check

Contributing to this project is easy, and reporting an issue or
adding to the documentation also improves things for every user.
You don’t need to be a developer to contribute.
See :doc:`CONTRIBUTING` for more.


Documentation Contents
----------------------

.. toctree::
    :maxdepth: 4

    usage
    api-reference
    CONTRIBUTING
    LICENSE


References
----------

Tools
^^^^^

-  `Cookiecutter <http://cookiecutter.readthedocs.org/en/latest/>`_
-  `PyInvoke <http://www.pyinvoke.org/>`_
-  `pytest <http://pytest.org/latest/contents.html>`_
-  `tox <https://tox.readthedocs.org/en/latest/>`_
-  `Pylint <http://docs.pylint.org/>`_
-  `twine <https://github.com/pypa/twine#twine>`_
-  `bpython <http://docs.bpython-interpreter.org/>`_
-  `yolk3k <https://github.com/myint/yolk#yolk>`_

Packages
^^^^^^^^

-  `Rituals <https://jhermann.github.io/rituals>`_
-  `Click <http://click.pocoo.org/>`_


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
