#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
import random

BASE =  os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
DELIMITER = "_"


def cleanup(tokens):
    """cleanup a sentence by capitalizing the first letter, remove conjuctions like "and" and "to"
    from the end and add a punctuation mark.
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

    # Replace opening parathesis with a comma and remove closing paranthesesis and
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
    if not text.endswith((".", "!", "?", "...")):
        rand = random.random()
        if rand < 0.81:
            end = "."  # "." should have the greatest change of getting selected
        else:
            end = random.choice(("!", "?", "..."))  # choose evenly between the rest

        text += end

    return text