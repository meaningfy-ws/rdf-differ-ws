#!/usr/bin/python3

# latex_utils.py
# Date:  05/01/2021
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

"""
Latex parsing functionality

This module provides functions to parse latex text

Credits: This module was adapted after the Samuel Roeca's latex repository (pappasam/latexbuild on github)
"""

import re

# Organize all latex escape characters in one list
# (EXCEPT FOR ( "\" ), which is handled separately)
# escaping those which are special characters in
# PERL regular expressions
ESCAPE_CHARS = [r'\&', '%', r'\$', '#', '_', r'\{', r'\}', '~', r'\^', ]

# For each latex escape character, create a regular expression
# that matches all of the following criteria
# 1) one or two characters
# 2) if two characters, the first character is NOT a backslash ( "\" )
# 3) if two characters, the second, if one, the first character
#       is one of the latex escape characters
REGEX_ESCAPE_CHARS = [
    (re.compile(r"(?<!\\)" + i), r"\\" + i.replace('\\', ''))
    for i in ESCAPE_CHARS
]

# Place escape characters in [] for "match any character" regex
ESCAPE_CHARS_OR = r'[{}\\]'.format(''.join(ESCAPE_CHARS))

# For the back slash, create a regular expression
# that matches all of the following criteria
# 1) one, two, or three characters
# 2) the first character is not a backslash
# 3) the second character is a backslash
# 4) the third character is none of the ESCAPE_CHARS,
#       and is also not a backslash
REGEX_BACKSLASH = re.compile(r'(?<!\\)\\(?!{})'.format(ESCAPE_CHARS_OR))


def escape_latex(value: str):
    """
        Escape a latex string
    :param value:
    :return:
    """

    if not isinstance(value, str):
        return value
    for regex, replace_text in REGEX_ESCAPE_CHARS:
        value = re.sub(regex, replace_text, value)
    value = re.sub(REGEX_BACKSLASH, r'\\\\', value)
    return value
