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

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .model.propertyBase import Cardinality, TypeID


class ToolError(BaseModel):
    """
    Represents an error response from a tool execution.

    This class helps the LLM understand error messages and provides suggestions
    for potential resolutions.
    """

    isError: Literal[True] = Field(
        default=True,
        description="Indicates that an error occurred during tool execution if value is True",
    )

    message: str = Field(description="Detailed error message")

    suggestions: List[str] = Field(
        default_factory=list, description="List of suggestions for resolving the error"
    )


class SearchOperator(str, Enum):
    """
    Enum defining all valid search operators for repository searches.

    These operators determine how property values are compared during searches.
    """

    EQUALS = "="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    NOT_EQUAL = "!="
    CONTAINS = "CONTAINS"
    STARTS_WITH = "STARTS"
    ENDS_WITH = "ENDS"


class SearchProperty(BaseModel):
    """
    Defines a single search condition/filter to be applied during repository searches.
    """

    property_name: str = Field(
        ...,
        description="The name of the property to filter on. Must be a valid property for the specified class as obtained from the get_searchable_class_properties_tool .",
    )
    property_value: str = Field(
        ...,
        description="The value to filter by. Format should match the property's data type.",
    )
    operator: SearchOperator = Field(
        ...,
        description="The comparison operator that defines how property_name and property_value are compared. "
        "Use CONTAINS for substring matching, STARTS/ENDS for prefix/suffix matching. "
        "Use standard SQL operators: =, >, <, >=, <=, != for other properties.",
    )


class SearchParameters(BaseModel):
    """
    Complete set of parameters for executing a repository search.
    """

    search_class: str = Field(
        ...,
        description="The class to search for. Must be a valid class in the repository.",
    )
    search_properties: List[SearchProperty] = Field(
        ...,
        description="List of filter conditions to apply to the search. All conditions are combined with AND logic. If no conditions exist, we return all objects of the given class",
    )


class CachePropertyDescription(BaseModel):
    """Describes detailed attributes or metadata about a property."""

    symbolic_name: str = Field(
        description="Symbolic name that is used to reference this property"
    )
    display_name: str = Field(description="A user displayable name for this property")
    descriptive_text: str = Field(
        description="Describes additional details about this property"
    )
    data_type: TypeID = Field(description="The type of data this property can hold")
    cardinality: Cardinality = Field(
        description="Whether this property holds a single value or multiple values."
    )
    is_searchable: bool = Field(
        description="Indicates whether searches can include conditions involving this property"
    )
    is_system_owned: bool = Field(
        default=False, description="Indicates whether this property is system-owned"
    )
    is_hidden: bool = Field(
        default=False, description="Indicates whether this property is hidden"
    )
    valid_search_operators: List[SearchOperator] = Field(
        description="The valid operators that can be used with this property in a search condition"
    )


class ClassDescriptionData(BaseModel):
    """Information about a class in the content repository."""

    display_name: str = Field(description="The display name of the class")
    symbolic_name: str = Field(
        description="Symbolic name that is used to reference this class"
    )
    descriptive_text: str = Field(
        description="Describes additional details about this class"
    )


class CacheClassDescriptionData(ClassDescriptionData):
    """Information about a class in the content repository."""

    name_property_symbolic_name: Optional[str] = Field(
        description="The symbolic name of the property that provides the name of an object of this class"
    )
    property_descriptions: List[CachePropertyDescription] = Field(
        description="List of all properties of this class"
    )


class CachePropertyDescriptionBooleanData(CachePropertyDescription):
    property_default_boolean: Optional[bool] = None


class CachePropertyDescriptionDateTimeData(CachePropertyDescription):
    is_date_only: bool
    property_default_date_time: Optional[datetime] = None
    property_maximum_date_time: Optional[datetime] = None
    property_minimum_date_time: Optional[datetime] = None


class CachePropertyDescriptionFloat64Data(CachePropertyDescription):
    property_default_float64: Optional[float] = None
    property_minimum_float64: Optional[float] = None
    property_maximum_float64: Optional[float] = None


class CachePropertyDescriptionIdData(CachePropertyDescription):
    property_default_id: Optional[uuid.UUID] = None


class CachePropertyDescriptionInteger32Data(CachePropertyDescription):
    property_default_integer32: Optional[int] = None
    property_maximum_integer32: Optional[int] = None
    property_minimum_integer32: Optional[int] = None


class CachePropertyDescriptionStringData(CachePropertyDescription):
    maximum_length_string: Optional[int] = None
    property_default_string: Optional[str] = None
