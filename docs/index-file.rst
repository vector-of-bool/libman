.. _lm.index:

The Index File
##############

.. note::
    Read :ref:`lm.format` first.

The purpose of the *index* file is to specify the mapping between package names
and the location of their respective :ref:`package files <lm.package>` on disk.

The file extension of an index file is ``.lmi``.


Fields
******


``Type``
========

The ``Type`` field in an index file *must* be ``Index``, and must appear
*exactly once*::

    Type: Index


``Package``
===========

The ``Package`` field appears any number of times in a file, and specifies a
package *name* and a *path* to a :ref:`package file <lm.package>` on disk. If
a relative path, the path resolves relative to the directory containing the
index file.

The name and path are separated by a semicolon ``;``. Extraneous whitespace
is stripped::

    Package: Boost; /path/to/boost.lmp
    Package: Qt; /path-to/qt.lmp
    Package: POCO; /path-to-poco.lmp
    Package: SomethingElse; relative-path/anything.lmp

The appearance of two ``Package`` fields with the same package name is not
allowed and consumers should produce an **error** upon encountering it.


Example
*******

.. code-block:: yaml

    # This is an index file
    Type: Index

    # Some Packages
    Package: Boost; /path/to/boost.lmp
    Package: Qt; /path-to/qt.lmp
    Package: POCO; /path-to-poco.lmp
    Package: SomethingElse; relative-path/anything.lmp


Rationale and Intended Usage
****************************

A index file is intended to be produced by a tool automatically to provide a
consumer with a complete, consistent, and coherent view of a package hierarchy.

**Note the lack of version or ABI information.** It is up to the generating
tool to ensure that the packages listed therein have consistent ABIs and
version compatibilities. It is not the concern of the consumer to perform ABI
and version resolution.

.. note::

    By implication, a single binary should be able to simultaneously link to
    *every library and every package* reachable via a single index file without
    encountering any ABI or version conflicts.

    However, *libman* specifically facilitates pick-and-choose linking on a
    per-target basis. Build systems should only use the *minimum* required
    based on what is explicitly requested by the user for each target.
