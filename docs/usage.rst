..  documentation: usage

    Copyright ©  2015 1&1 Group <git@1and1.com>

    ## LICENSE_SHORT ##
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

=============================================================================
Using Confluencer
=============================================================================

Providing Login Credentials
---------------------------

Before you can use *Confluencer*, you have to provide some minimal
configuration, most importantly credentials for API access.
Select one of the ways outlined below to store your API credentials.

Using the ~/.netrc File
^^^^^^^^^^^^^^^^^^^^^^^

 1. Create the file ``~/.netrc`` with the following contents (or add that
    to the existing file):

    ..  code-block:: aconf

        machine confluence.example.org
            login «your username»
            password «your password»

 2. Call ``chmod 600 ~/.netrc`` to protect your sensitive data.

 3. Check that everything is OK by calling ``python3 -m netrc | less``.

This way, the sensitive authentication information is separate from the
rest of the configuration. Use the ``cfr help`` command to check whether
your credentials actually work – if they do, the “Confluence Stats”
section in the output will show some basic info about your wiki,
otherwise you'll see an error indicator.


Using a Keyring Query Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**TODO**

Tools that can be used on Linux are ``gnome-keyring-query``
and `gkeyring <https://github.com/kparal/gkeyring>`_.



Cleaning Up Pages After Content Migration
-----------------------------------------

The *Confluence* rich text editor allows you to migrate content
from rendered HTML in other systems by simple copy&paste.
However, certain artifacts of the source system are carried over,
or active content is only copied with its *current (static) state*.

The ``cfr tidy`` sub-command relieves you from manually fixing all those tiny
defects, based on built-in patterns and replacement rules.
These rules currently target *FosWiki* as a source, and for example
a copied table of contents is replaced by the related *Confluence* macro.

Pass it the URL of the page you want to clean up – adding the ``--recursive``
option includes all descendants of that page. Normally, the output
shows which and how often rules are applied to the content, the ``--diff`` option
adds a detailed record of the applied changes.

If you want to just show the changes without applying them, use the
``--no-save`` option (or the shorter ``-n``). This automatically includes
diff output, to just show the applied rules repeat the option (``-nn``).

.. code::

    $ cfr tidy -nn "http://confluence.local/display/~jhe/Sandbox"
    INFO:confluencer:Replaced 2 matche(s) of "FosWiki: Empty anchor in headers" (16 chars removed)
    INFO:confluencer:Replaced 3 matche(s) of "FosWiki: 'tok' spans in front of headers" (94 chars removed)
    INFO:confluencer:Replaced 3 matche(s) of "FosWiki: Section edit icons at the end of headers" (664 chars removed)
    INFO:confluencer:Replaced 1 matche(s) of "FosWiki: Replace TOC div with macro" (127 chars removed)
    INFO:confluencer:WOULD save page#2393332 "Sandbox" as v. 11


Exporting Metadata for a Page Tree
----------------------------------

:command:`cfr stats tree` generates a JSON list of a page tree given its root page
(other output formats will follow). You can then select more specific information
from that using ``jq`` or other JSON tools.

Consider this example creating a CSV file:

.. code-block:: console

    $ cfr stats tree "https://confluence.local/x/_EJN" \
      | jq '.[] | .depth, .title, .version.when, .version.by.displayName' \
      | paste -sd ';;;\n'
    INFO:confluencer:Got 21 results.
    0;"Root Page";"2016-10-24T17:20:04.000+02:00";"Jürgen Hermann"
    1;"First Immediate Child";"2020-01-22T14:24:45.111+01:00";"Jürgen Hermann"
    …
