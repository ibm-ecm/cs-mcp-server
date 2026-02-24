# Copyright contributors to the IBM Core Content Services MCP Server project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from enum import Enum
from typing import Optional, Self
from datetime import datetime

from pydantic import BaseModel, Field


class HoldableRootClassEnum(str, Enum):
    Document = "Document"
    Annotation = "Annotation"
    Folder = "Folder"
    CustomObject = "CustomObject"
    Unknown = "Unknown"

class HeldObject(BaseModel):
    """
    A HeldObject class
    """ 

    system_root_class_name: HoldableRootClassEnum = Field( description="The symbolic name of the root class of the held object.") 
    class_name: str = Field(description="The class name of the held object.")
    name: str = Field(description="The name of the held object.")
    id: str = Field(description="The id of the held object.")  
    date_created: Optional[datetime] = Field(
        default=None, description="Date when the held object was created"
    )
    date_last_modified: Optional[datetime] = Field(
        default=None, description="Date when the held object was last modified"
    )

    @classmethod
    def create_an_instance(cls, graphQL_changed_object_dict: dict) -> Self : 
        """Create a HeldObject instance from a GraphQL Document"""

        # init the held_object dict
        held_object = {}

        properties = graphQL_changed_object_dict["properties"] 
        for prop in properties: 
            if prop["id"] == "HeldObject": 

                held_object["id"] = prop["value"]["identifier"] 

                # get the system root class name based on alias key
                object_value = prop["objectValue"]
                held_object["system_root_class_name"] = HoldableRootClassEnum.Unknown
                if "documentId" in object_value:
                    held_object["system_root_class_name"] = HoldableRootClassEnum.Document
                if "annotationId" in object_value:
                    held_object["system_root_class_name"] = HoldableRootClassEnum.Annotation
                if "customObjectId" in object_value:
                    held_object["system_root_class_name"] = HoldableRootClassEnum.CustomObject
                if "folderId" in object_value:
                    held_object["system_root_class_name"] = HoldableRootClassEnum.Folder

                
                held_object["class_name"] = object_value["className"]
                held_object["name"] = object_value["name"]
                held_object["date_created"] = object_value["dateCreated"]
                held_object["date_last_modified"] = object_value["dateLastModified"]

  

        return cls(**held_object)



class HoldRelationship(BaseModel):
    """
    A hold relationship class
    """

    hold_relationship_id: str = Field(
        description="The id of the hold relationship object."
    )
    held_id: str = Field(description="The id of the held object.")

    held_root_class: HoldableRootClassEnum = Field(
        description="The symbolic name of the root class of the held object."
    )

    hold_id: str = Field(description="The id of the hold object.")
    creator: str = Field(description="The creator of this hold relationship object.")
    last_modifier: str = Field(
        description="The last modifier of this hold relationship object."
    )

    @classmethod
    def create_an_instance(cls, graphQL_changed_object_dict: dict):
        properties = graphQL_changed_object_dict["properties"]
        hold_relationship = {} # initialize a dictionary to hold the hold relationship object
        for prop in properties:
            if prop["id"] == "HeldObject":
                hold_relationship ["held_id"] = prop["value"]["identifier"]
                hold_relationship ["held_root_class"] = prop["value"]["classIdentifier"]
            if prop["id"] == "Hold":
                hold_relationship ["hold_id"] = prop["value"]["identifier"]
            if prop["id"] == "Id":
                hold_relationship ["hold_relationship_id"] = prop["value"]
            if prop["id"] == "Creator":
                hold_relationship ["creator"] = prop["value"]
            if prop["id"] == "LastModifier":
                hold_relationship ["last_modifier"]= prop["value"]
        return cls( ** hold_relationship )


class Hold(BaseModel):
    """
    A hold class
    """

    hold_display_name: str = Field(description="The display name of the hold.")
    hold_id: str = Field(description="The id of the hold object.")
    creator: str = Field(description="The creator of this hold relationship object.")
 

    @classmethod
    def create_an_instance(cls, graphQL_changed_object_dict: dict):
        properties = graphQL_changed_object_dict["properties"]
        hold  = {}

        for prop in properties:
            if prop["id"] == "Id":
                hold ["hold_id"] = prop["value"]
            if prop["id"] == "DisplayName":
                hold["hold_display_name"] = prop["value"]
            if prop["id"] == "Creator":
                hold["creator"]  = prop["value"]

        return cls(**hold)

