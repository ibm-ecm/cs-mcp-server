#  Licensed Materials - Property of IBM (c) Copyright IBM Corp. 2025 All Rights Reserved.

#  US Government Users Restricted Rights - Use, duplication or disclosure restricted by GSA ADP Schedule Contract with
#  IBM Corp.

#  DISCLAIMER OF WARRANTIES :

#  Permission is granted to copy and modify this Sample code, and to distribute modified versions provided that both the
#  copyright notice, and this permission notice and warranty disclaimer appear in all copies and modified versions.

#  THIS SAMPLE CODE IS LICENSED TO YOU AS-IS. IBM AND ITS SUPPLIERS AND LICENSORS DISCLAIM ALL WARRANTIES, EITHER
#  EXPRESS OR IMPLIED, IN SUCH SAMPLE CODE, INCLUDING THE WARRANTY OF NON-INFRINGEMENT AND THE IMPLIED WARRANTIES OF
#  MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT WILL IBM OR ITS LICENSORS OR SUPPLIERS BE LIABLE FOR
#  ANY DAMAGES ARISING OUT OF THE USE OF OR INABILITY TO USE THE SAMPLE CODE, DISTRIBUTION OF THE SAMPLE CODE, OR
#  COMBINATION OF THE SAMPLE CODE WITH ANY OTHER CODE. IN NO EVENT SHALL IBM OR ITS LICENSORS AND SUPPLIERS BE LIABLE
#  FOR ANY LOST REVENUE, LOST PROFITS OR DATA, OR FOR DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
#  DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, EVEN IF IBM OR ITS LICENSORS OR SUPPLIERS HAVE
#  BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

"""
Scoring utilities for matching objects based on keywords.

This module provides common scoring functionality used across different parts
of the application for matching objects (classes, documents, etc.) against keywords.
"""

from .constants import (
    SUBSTRING_SIMILARITY_MULTIPLIER,
    PREFIX_SIMILARITY_MULTIPLIER,
)


# Helper function for word tokenization
def tokenize(text):
    """Split text into words, handling CamelCase and snake_case"""
    # Handle CamelCase by inserting spaces before capital letters
    text = "".join([" " + c if c.isupper() else c for c in text]).strip()
    # Handle snake_case by replacing underscores with spaces
    text = text.replace("_", " ")
    # Split by spaces and filter out empty strings
    return [word.lower() for word in text.split() if word]


# Helper function for calculating word similarity (simple fuzzy matching)
def word_similarity(word1, word2):
    """Calculate similarity between two words (0-1)"""
    # If words are identical, return 1.0
    if word1 == word2:
        return 1.0

    # If one word is a substring of the other, return high similarity
    if word1 in word2:
        return SUBSTRING_SIMILARITY_MULTIPLIER * (len(word1) / len(word2))
    if word2 in word1:
        return SUBSTRING_SIMILARITY_MULTIPLIER * (len(word2) / len(word1))

    # Count matching characters at the beginning
    prefix_match = 0
    for i in range(min(len(word1), len(word2))):
        if word1[i] == word2[i]:
            prefix_match += 1
        else:
            break

    # Return similarity based on prefix match length
    if prefix_match > 0:
        return PREFIX_SIMILARITY_MULTIPLIER * (
            prefix_match / max(len(word1), len(word2))
        )

    return 0.0
