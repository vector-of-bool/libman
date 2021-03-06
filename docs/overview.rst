A ``libman`` Overview
#####################

What is "libman?" It's a shortening of "library manifest." It's a combination of
file format and design specification to bridge the gap between build systems
and package/dependency managers (PDMs).

Goals
*****

The following are the explicit goals of *libman*:

1. Define a series of file formats which tell a build system how a library is
   "used"
2. Define the semantics of how a build system should interact and perform
   name-based package and dependency lookup in a deterministic fashion with no
   dependence on "ambient" environment state
3. Implement minimal tools and libraries for consuming and generating the files
   defined by *libman*

Non-Goals
*********

Perhaps just as important as the goals are the *non-goals.* In particular,
*libman does not* seek to do any of the following:

1. Define the semantics of ABI and version compatibility between libraries
2. Facilitate dependency resolution beyond trivial name-based path lookup
3. Define a distribution or packaging method for pre-compiled binary packages
4. Define or aide package retrieval and extraction
5. Define or aide source-package building

The Format
**********

*libman* defines a file format and schema for the files that will be consumed
by a build system or generated by a PDM. See the :ref:`lm.files` page for
details.

