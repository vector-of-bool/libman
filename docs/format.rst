.. _lm.format:

Base File Format
################

All *libman* files are encoded in an extremely simple key-value plaintext
format, which is easy to read and write for human and machine alike.

Syntax
******

The syntax of the file is very simple:

.. code-block:: yaml

    # This is a comment
    Some-Key: Some-Value

Keys and values in the file each appear on a different line, with the key and
value being separated by a ": " (colon followed by a space). Only a single space
after the colon is required. Trailing or leading whitespace from the keys and
values is ignored. If a colon is followed by an immediate line-ending,
end-of-file, or the right-hand of the key-value separator is only whitespace,
the value for the associated key is an empty string. Note that a colon *is
allowed* to be a character in a key (but cannot be the final character).

The key and value together form a "field."

**KEYS AND VALUES ARE CASE-SENSITIVE.**

A field *might* appear multiple times in the file. The semantics thereof depend
on the semantics of the field.

Each file in *libman* defines a set of acceptable fields. The appearance of
unspecified fields is not allowed, and should be met with a user-visible warning
(but *not an error*). There is an exception for keys beginning with `X-`, which
are reserved for tool-specific extensions. The presence of an unrecognized key
beginning with `X-` is not required to produce a warning.

Lines in which the first non-whitespace character is a ``#`` should be ignored.

"Trailing comments" are not supported. A ``#`` appearing in a key or value
must be considered a part of that key or value.

Empty or only-whitespace lines are ignored.

Readers are expected to accept a single line feed ``\n`` as a valid line-ending.
Because trailing whitespace is stripped, a CR-LF ``\r\n`` is *incidentally* a
valid line-ending and should result in an identical parse.

A line-ending is not required at the end of the file.
