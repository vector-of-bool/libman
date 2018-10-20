.. _lm.package:

Package Files
#############

.. note::
    Read :ref:`lm.format` first.

A *package* is a collection that contains one or more *libraries* that are
distributed and built as a unit. The package file describes the contents of a
single package.

The file extension of a package file is ``.lmp``.


Fields
******


``Type``
========

The ``Type`` field in a package file *must* be ``Package``, and must appear
*exactly once*::

    Type: Package


``Name``
========

The ``Name`` field in a package file should be the name of the package, and
*should* match the name of the package present in the :ref:`index <lm.index>`
that points to the file defining the package. If ``Name`` is not present or not
equal to the name provided in the index, consumers are not required to generate
a warning. It's purpose is for the querying of individual package files and for
human consumption.

::

    Name: Boost


``Namespace``
=============

The ``Namespace`` field in a package file is require to appear *exactly once*.
It is not required to correspond to any C++ ``namespace``, and is purely for the
namespaces of the import information for consuming tools. For example, CMake
will prepend the ``Namespace`` and two colons ``::`` to the name of imported
targets generated from the *libman* manifests.

::

    Namespace: Qt5

.. note::
    The namespace is not required to be unique between packages. Multiple
    packages may declare themselves to share a ``Namespace``, such as for
    modularized Boost packages.


``Requires``
============

The ``Requires`` field may appear multiple times, each time specifying the name
of a package which is required in order to use the requiring package.

When a consumer encounters a ``Requires`` field, they should use the
:ref:`index file <lm.index>` to find the package specified by the given name.
If no such package is listed in the index, the consumer should generate an
error.

::

    Requires: Boost.Filesystem
    Requires: Boost.Coroutine2
    Requires: fmtlib


``Library``
===========

The ``Library`` field specifies the path to a :ref:`library file <lm.library>`.
Each appearance of the ``Library`` field specifies another library which should
be considered as part of the package.

::

    Library: filesystem.lml
    Library: system.lml
    Library: coroutine2.lml

If a relative path, the file path should be resolved relative to the directory
of the package file.

.. note::
    The filename of a ``Library`` field is not significant.


Example
*******

.. code-block:: yaml

    # A merged Qt5
    Type: Package
    Name: Qt5
    Namespace: Qt5

    # Some things we might require
    Requires: OpenSSL
    Requires: Xcb

    # Qt libraries
    Library: Core.lml
    Library: Widgets.lml
    Library: Gui.lml
    Library: Network.lml
    Library: Quick.lml
    # ... (Qt has many libraries)


Rationale and Intended Usage
****************************

While many projects out there will only expose a single library, it is important
to support the use case of frameworks both large and small. We can't assume that
a single package exposes a single consumable/linkable, nor can we assume that
a package exports something linkable *at all.* For example, a package may be
distributed only to contain enhancements to an underlying build tool,
to enable code generation (Done using ``X-`` "extension fields"), or to act as
"meta" packages meant to purely depend on a collection of other packages.

The ``Namespace`` field is meant to allow individual libraries to use
unqualified names without colliding with a global names.

Upon importing the usage requirements of the libraries within a package, the
identities of the imported libraries should be qualified the the ``Namespace``
of the package in which the library is defined.

The package files may or may not be generated on-the-fly by a tool, either at
install time or build time. The package files may also be hand-written and
bundled with the binary distribution of the package. This can be useful for
closed-source packages that wish to distribute a package which is compatible
with *libman*-aware build systems and dependency managers.
