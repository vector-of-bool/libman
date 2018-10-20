.. _lm.library:

Library Files
#############

.. note::
    Read :ref:`lm.format` first.

A *library* is a reusable unit of code that can be consumed by an external
project. It has some number of directories for headers and linkables. A library
file describes how build systems should integrate a library in their targets.

The file extension of a library file is ``.lml``.


Fields
******


``Type``
========

The ``Type`` field in a library file *must* be ``Library``, and must appear
*exactly once*::

    Type: Library


``Name``
========

The ``Name`` field must appear *exactly once*. Consumers should qualify this
name and the containing package's ``Namespace`` field to form the identifier
for the library.

::

    Name: system


``Path``
========

For libraries which provide a linkable, the ``Path`` field specifies the path
to a file which should be linked into executable binaries. This may be a static
or dynamic library.

This field may be omitted for libraries which do not have a linkable (e.g.
"header-only" libraries).

::

    Path: lib/libboost_system-mt-d.a


``Include``
===========

Specifies a directory path in which the library's headers can be found. Targets
which use this library should have the named directory appended to their header
search path. (e.g. using the ``-I`` or ``-isystem`` flag in GCC).

This field may appear any number of times. Each appearance will specify an
additional search directory.

Relative paths should resolve relative to the directory containing the library
file.

::

    Include: include/
    Include: src/


``Define``
==========

Sets a preprocessor define that is required to use the library.

.. note::
    This should not be seen as an endorsement of this design. The author would
    prefer that libraries use a "config header" than to require their consumers
    to set preprocessor definitions.

    Nevertheless: people do it, so we support it.

Should be either a legal C identifier, or a C identifier and substitution value
separated with an ``=``. (The syntax used by MSVC and GNU-style compiler command
lines).

::

    Define: SOME_LIBRARY
    Define: SOME_LIBRARY_VERSION=339


``Uses``
========

Specify a *transitive requirement* for using the library. This must be of the
format ``<namespace>/<library>``, where ``<namespace>`` is the string used in
the ``Namespace`` field of the package which defines ``<library>``, and
``<library>`` is the ``Name`` field of the library which we intend to use
transitively.

::

    Uses: Boost/coroutine2
    Uses: Boost/system

Build systems should use the ``Uses`` field to apply transitive imported
library target usage requirements. "Using" targets should transitively "use"
the libraries named by this field.


``Links``
=========

Specifiy a *transitive linking requirement* for using the library. This is
the same format and intention for ``Uses`` field, but only the transitive usage
requirements related to linking need to be propagated.

.. note::
    This may not be implementable distinctly from ``Uses`` on some build
    systems. In such a case, the behavior should be the same as the ``Uses``
    field.

::

    Links: Boost/system
    Links: Qt5/Core

