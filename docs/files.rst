.. _lm.files:

*libman* Files
##############

*libman* defines a few files, all using a simple :ref:`key-value plaintext file
format <lm.format>`:

- :ref:`The Index <lm.index>` - Defines the mapping between package names and
  the path to the package files on disk.
- :ref:`Package Files <lm.package>` - Defines importable *packages*. Each
  package may itself define one or more *libraries*.
- :ref:`Library Files <lm.library>` - Each defining a single importable library.

None of the files may be consumed individually since the files can (and will)
refer to each-other. See the individual file documentation pages for details.

Table of Contents
-----------------

.. toctree::
    :maxdepth: 2

    format
    index-file
    package-file
    library-file
