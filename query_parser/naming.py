"""Support for naming expressions

In order to use elastic search named query, we need to be able to assign names to expressions
and retrieve their positions in the query text.

This module adds support for that.
"""

#: Names are added to tree items via an attribute named `_luqum_name`
NAME_ATTR = "_luqum_name"


def set_name(node, value):
    setattr(node, NAME_ATTR, value)


def get_name(node):
    return getattr(node, NAME_ATTR, None)
