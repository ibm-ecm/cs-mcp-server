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

from enum import Enum

from pydantic import BaseModel, Field


class HoldableRootClassEnum(str, Enum):
    Document = "Document"
    Annotation = "Annotation"
    Folder = "Folder"
    CustomObject = "CustomObject"


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
        for prop in properties:
            if prop["id"] == "HeldObject":
                held_id = prop["value"]["identifier"]
                held_root_class = prop["value"]["classIdentifier"]
            if prop["id"] == "Hold":
                hold_id = prop["value"]["identifier"]
            if prop["id"] == "Id":
                hold_relationship_id = prop["value"]
            if prop["id"] == "Creator":
                creator = prop["value"]
            if prop["id"] == "LastModifier":
                last_modifier = prop["value"]
        return cls(
            hold_id=hold_id,
            held_id=held_id,
            held_root_class=held_root_class,
            hold_relationship_id=hold_relationship_id,
            creator=creator,
            last_modifier=last_modifier,
        )
