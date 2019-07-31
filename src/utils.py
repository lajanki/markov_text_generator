#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import random

BASE =  os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DELIMITER = "_"


def cleanup(tokens):
    """cleanup a sentence by capitalizing the first letter, remove certain characters such as
    parenthesis which are difficult to properly handle on random text generation.
    Arg:
        tokens (list): the sentence to normalize as a list of words
    Return:
        the normalized sentence as a string
    """
    # Capitalize and strip the first word (calling capitalize() on the whole string would
    # decapitalize everyting else).
    tokens[0] = tokens[0].capitalize().strip()
    text = " ".join(tokens)
    text = text.lstrip(" -*")

    # Replace opening parathesis with a comma and remove closing paranthesesis.
    # replace other inconvenient characters.
    replacements = [
        (" (", ","),
        ("(", ""), # in case the first character of a sentence is "("
        (")", ""),
        ("\"", ""),
        (u"“", ""),
        (u"”", ""),
        (u"”", ""),
        (u"•", ""),
        (u"●", ""),
        (u"—", ""),
        (u"…", "...")
    ]
    for item in replacements:
        text = text.replace(item[0], item[1])


    text = text.rstrip(",;:- ")
    return text