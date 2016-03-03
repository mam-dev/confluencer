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
