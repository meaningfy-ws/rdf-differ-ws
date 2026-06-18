#!/usr/bin/python3

# __init__.py
# Date:  07/08/2020
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com
import collections
from typing import List, Dict


def sort_by_size_and_alphabet(l: List) -> List:
    """
        Sort an iterable by size and alphabetically
    :param l:
    :return:
    """
    return sorted(l, key=lambda x: (len(x), x))


def first_key(d: (Dict, None)) -> object:
    """
        Return the first dict key that from all the keys ordered first by their length and then alphabetically.
    """
    return sort_by_size_and_alphabet(list(d.keys()))[0] if d else None


def first_key_value(d: (Dict, None)) -> object:
    """
        Return the dict value for the first key in the dict;
        The first key is determined using `first_key` function.
    """
    return d[first_key(d)] if d else None


def invert_dict(mapping_dict: Dict, reduce_values: bool = True):
    """
        Invert the dictionary by swapping keys and values. In case the values are unique then the inverted dict will be
        of the same size as the initial one. Otherwise it will be shrunk to the unique values and the keys will be
        cumulated in a list.

        The list can be reduced to single item by setting reduce_values=True.

        >>> d = {"a":1, "b":2, "c":1}
        >>> reduced_d = invert_dict(d)
        {1: 'a', 2: 'b'}

        >>> unreduced_d = invert_dict(d, False)
        {1: ['a', 'c'], 2: ['b']}

        :param reduce_values: If reduce_values is true then the values are single items otherwise
                                the values are list of possibly multiple items.
        :type mapping_dict: a dictionary to be inverted
    """
    inv_map = {}
    for k, v in mapping_dict.items():
        inv_map[v] = inv_map.get(v, [])
        inv_map[v].append(k)
    if reduce_values:
        return {k: sort_by_size_and_alphabet(v)[0] for k, v in inv_map.items()}
    return inv_map


def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modify ``source`` in place.

    Used from https://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
    """
    for key, value in overrides.items():
        if isinstance(value, collections.abc.Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]
    return source
