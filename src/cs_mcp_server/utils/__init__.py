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
Utilities module for MCP servers.

This module provides common utility functions and models.
"""

from .common import (
    ToolError,
    SearchOperator,
    SearchProperty,
    SearchParameters,
    CachePropertyDescription,
    ClassDescriptionData,
    CacheClassDescriptionData,
    CachePropertyDescriptionBooleanData,
    CachePropertyDescriptionDateTimeData,
    CachePropertyDescriptionFloat64Data,
    CachePropertyDescriptionIdData,
    CachePropertyDescriptionInteger32Data,
    CachePropertyDescriptionStringData,
)
from .model.admin import HoldRelationship
from .model.propertyBase import TypeID, Cardinality
from .model.core import Document
from .model.coreInput import (
    DocumentPropertiesInput,
    SubCheckinActionInput,
    SubCheckoutActionInput,
    ReservationType,
    ContentElementType,
    BaseContentElementInput,
    ContentElementListInput,
    InsertDependentActionInput,
    SubContentTransferInput,
)

# Import commonly used constants for convenience
from .constants import (
    DEFAULT_DOCUMENT_CLASS,
    DEFAULT_FOLDER_CLASS,
    VERSION_SERIES_CLASS,
    TEXT_EXTRACT_ANNOTATION_CLASS,
    CM_HOLD_CLASS,
    CM_HOLD_RELATIONSHIP_CLASS,
    EXACT_SYMBOLIC_NAME_MATCH_SCORE,
    EXACT_DISPLAY_NAME_MATCH_SCORE,
    HIGH_SIMILARITY_THRESHOLD,
    MEDIUM_SIMILARITY_THRESHOLD,
    MAX_SEARCH_RESULTS,
    TRACEBACK_LIMIT,
)

__all__ = [
    "ToolError",
    "SearchOperator",
    "SearchProperty",
    "SearchParameters",
    "TypeID",
    "Cardinality",
    "CachePropertyDescription",
    "ClassDescriptionData",
    "CacheClassDescriptionData",
    "CachePropertyDescriptionBooleanData",
    "CachePropertyDescriptionDateTimeData",
    "CachePropertyDescriptionFloat64Data",
    "CachePropertyDescriptionIdData",
    "CachePropertyDescriptionInteger32Data",
    "CachePropertyDescriptionStringData",
    "HoldRelationship",
    "Document",
    "DocumentPropertiesInput",
    "SubCheckinActionInput",
    "SubCheckoutActionInput",
    "ReservationType",
    "ContentElementType",
    "BaseContentElementInput",
    "ContentElementListInput",
    "InsertDependentActionInput",
    "SubContentTransferInput",
    # Constants
    "DEFAULT_DOCUMENT_CLASS",
    "DEFAULT_FOLDER_CLASS",
    "VERSION_SERIES_CLASS",
    "TEXT_EXTRACT_ANNOTATION_CLASS",
    "CM_HOLD_CLASS",
    "CM_HOLD_RELATIONSHIP_CLASS",
    "EXACT_SYMBOLIC_NAME_MATCH_SCORE",
    "EXACT_DISPLAY_NAME_MATCH_SCORE",
    "HIGH_SIMILARITY_THRESHOLD",
    "MEDIUM_SIMILARITY_THRESHOLD",
    "MAX_SEARCH_RESULTS",
    "TRACEBACK_LIMIT",
]
