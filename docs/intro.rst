Introduction
############

This page will give you an introduction to ``libman``. What is it? What problems
does it solve? etc.


Background
**********

C++ is late to the game in terms of a unified and cross-platform solution for
easily distributing native libraries.

There are "native" "system" package managers and package formats, such as
`dpkg`/`apt`, `yum`/`rpm`, `pacman`, and MSI that address a core problem of
managing the global state of a given machine, and these packaging formats often
deal with "native" compiled binaries. These solutions are *not* cross-platform,
and *even if they were*, **none** of them are appropriate for the problem at
hand. They are not focused on development and compilation within the C++
ecosystem. While other languages and ecosystems have tools such as ``pip``,
``npm``, ``cargo``, ``mix``, and even ``cpan``, C++ has gone a long time with
no widely-accepted solution.

Why is this?

There have been many attempts, and there are presently several competing
alternatives for solving the package and dependency management problem. Running
in parallel, and solving a (somewhat) orthogonal problem, are several competing
build systems. CMake, Meson, Waf, b2, and countless others have been pining for
the love and attention of the C++ community for years. All of them wildly
incompatible in terms of their package consumption formats.

This situation presents a unique problem. With lack of a "reference
implementation" of C++, and no singular and completely universal build tool and
format, we have an N:M problem of N package and dependency managers attempting
to work with M build systems.


Some Examples
*************

As an example, we will consider the way in which two popular package and
dependency managers work with CMake, a widely used C++ build system.


Using Conan with CMake
======================

Consider the following simple CMake project:

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.12)
    project(SomeProject VERSION 1.0.0)

    add_executable(my-program main.cpp)

    # Link to fmtlib ??

We want to use `fmtlib <http://fmtlib.net>`_ in our program. Let's write a
``conanfile.txt`` to do this:

.. code-block:: ini

    [requires]
    fmt/5.2.0@bincrafters/stable

    [generators]
    cmake

Now we need to install our dependencies with ``conan install .``. This will
place a ``conanbuildinfo.cmake`` file in the directory in which we run the
``conan install``. We must modify our CMake project to import this file
appropriately, and we can now link against ``fmtlib``:

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.12)
    project(SomeProject VERSION 1.0.0)

    include(conanbuildinfo.cmake)
    conan_basic_setup(TARGETS)

    add_executable(my-program main.cpp)

    target_link_libraries(my-program PRIVATE CONAN_PKGS::fmt)

Mmm... Despite the goal of keeping ourselves agnostic of a particular PDM, our
build system now explicitly requests Conan, and only works with Conan. The
correct thing is to use *conditional Conan support:*

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.12)
    project(SomeProject VERSION 1.0.0)

    if(EXISTS conanbuildinfo.cmake)
        include(conanbuildinfo.cmake)
        conan_basic_setup(TARGETS)
    endif()

    add_executable(my-program main.cpp)

    if(TARGET CONAN_PKGS::fmt)
        target_link_libraries(my-program PRIVATE CONAN_PKGS::fmt)
    else()
        # ... ?
    endif()

This *looks* like it works, but we've still got the problem of not having access
to `libfmt` when Conan isn't in use. For any alternative PDM we'd need to encode
additional logic to behave differently depending on what environment we are in.

.. note::
    This author is aware that *some* Conan packages will work with
    ``find_package()``, **but** this isn't universally available for all Conan
    packages, and it presents its own set of problems that make it insufficient.


Using ``vcpkg`` with CMake
==========================

Another popular PDM is ``vcpkg``, a tool from Microsoft that takes a different
approach to packaging. It won't be detailed in full here, as it is out-of-scope.

Here's our same CMake project, but using ``vcpkg`` to manage its dependencies:

.. code-block:: cmake

    cmake_minimum_required(VERSION 3.12)
    project(SomeProject VERSION 1.0.0)

    find_package(fmt REQUIRED)

    add_executable(my-program main.cpp)

    target_link_libraries(my-program PRIVATE fmt::fmt)

You'll notice the distinct lack of "vcpkg" being mentioned anywhere. This is
because vcpkg takes the idea of build systems and dependency management to its
fullest. To use vcpkg, you must invoke the tool outside of your build:

::

    $ vcpkg install fmt

And then invoke CMake using vcpkg's "toolchain" file:

::

    $ cmake -D CMAKE_TOOLCHAIN_FILE=/path/to/vcpkg/toolchain/vcpkg.cmake <source-dir>

This "toolchain" file is a way that vcpkg will "hook into" your build system the
first time CMake attempts to learn about the present compiler. The important
step (for our project) is that vcpkg modifies ``CMAKE_PREFIX_PATH`` such that
``find_package()`` will search in a vcpkg-generated directory where an
``fmtConfig.cmake`` file can be found. (The exact details of how this is done
and what a "packageConfig.cmake" file are is outside the scope of this
document).

In this way vcpkg is able to tweak the build system to be aware of vcpkg without
the user having to modify their build system.

It would seem vcpkg is surely superior. Right?

Not so fast! We still have a problem: ``find_package()`` works great *when it
works at all.*

``find_package()`` Finds Problems
=================================

Not all packages provide support for CMake's ``packageConfig.cmake`` format, and
even if they did it would still be CMake-specific. Library authors and/or
packagers would be forced to write and maintain these build-system-specific
integration files. No work that goes into writing ``fmtConfig.cmake`` does any
good for any build system besides CMake.

There are a few more problems with ``find_package()`` that become very prevalent
when we remove the PDM from the picture:

1. We search implicit global directories not controlled by a dependency manager
   (Not counting system package managers, which *are not developer tools* and
   should not be treated as such).
2. *Even if* a PDM is in use, a missing explicit requirement will cause
   ``find_package()`` to fall-through to search the system, when we want to
   keep all of our dependencies under the control of the PDM. ``find_package()``
   can successfully find system components when we meant to find PDM-controlled
   components, hiding missing requirements and dependency compatibility issues.
3. ``find_package()`` supports a ``VERSION`` argument, but it is *extremely
   poor* in its capability. It is entirely up to the package being found to
   respect the version request. It is perfectly valid for a found package to
   *completely ignore* our version request. Even if a package *does* honor this
   request, it may have different definitions of "compatible" between its
   version and the version we request.
4. If ``find_package()`` finds multiple compatible versions, it will simply pick
   the first version that was found during the scan. This can lead to
   non-deterministic versioning between builds.
5. ``find_package()`` has no sense of transitive dependencies.
6. ``find_package()`` has no sense of ABI compatibility.
7. ``find_package()`` does nothing to help with transitive versioning issues,
   e.g. "dependency diamonds."
8. ``find_package()`` does not enforce any semantics on the package being
   imported. Modern CMake packages will usually expose "imported targets," which
   present usage requirements and enforce dependency linking. This is *extremely
   helpful*, and is a desirable quality in a build system. Unfortunately,
   ``find_package()`` is merely a way to find a CMake script matching a certain
   file name, and executing it once it is found. ``find_package()`` essentially
   executes *arbitrary code*, and it will hopefully "do the right thing."

All of the above can be fixed and cobbled together on top of CMake's current
``packageConfig.cmake`` format (and has! This author has helped build and
maintain such a system for several years.)

**But none of it matters,** because none of it is portable. CMake *may* be
widely popular *today,* but committing to any specific build system could prove
fatal for a PDM.


Usage Requirements
******************

The concept of *usage requirements* originated from Boost's b2 build system,
and has been slowly bleeding into general acceptance via CMake. After years of
experience with CMake, and as it has been developing and maturing its
realization of *usage requirements* and the concept of the "usage interface,"
it is clear that it is *the* path forward. As such, ``libman`` is explicitly
designed around this concept.

What are "usage requirements" (also known as the "link interface" or "usage
interface")?

When we have a "target" (A thing that one wishes to build), we can say that it
"uses" a library. When we "use" a library, we need to inherit certain attributes
thereof which have a direct effect on the way that the final target will be
built. This includes, but is not limited to:

- **What header search paths do we need?** This ensures that the consumer target
  is able to ``#include`` the files from the library being consumed.
- **What files do we need to include in the link phase?** This ensures that
  entities with external linkage declared in the library's headers are available
  for symbol resolution during the final link.
- **What link/compile options are required?** In some rare cases, consuming a
  library will require that certain options be enabled/disabled on the compile
  or link phase. **This is not recommended, but is still very common.**
- **Who else do we need to "use"?** Library composition isn't a new idea, and
  it encourages modularity and encapsulation. To ensure that we are able to
  consume a library which builds upon another, we need to be sure that we can
  *also* use the transitive dependencies. This recurses through the "usage"
  directed graph until we have satisfied all the usage requirements for a tree.

``libman`` defines a platform-agnostic and build-system-agnostic format for
describing these "usage requirements", including how we can import dependencies
transitively. Any build system which can represent the above concepts can import
``libman`` files. Any PDM which can represent the above concepts can generate
``libman`` files.

Therefore, any ``libman``-capable build system can be used with any
``libman``-capable package and dependency manager.
