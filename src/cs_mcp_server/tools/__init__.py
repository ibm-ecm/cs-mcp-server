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

"""
Tools module for MCP servers.

This module exports all tool registration functions from the tools directory.
"""

# Import all registration functions to make them available when importing from this package
from .classes import register_class_tools
from .search import register_search_tools
from .legal_hold import register_hold_tools
from .vector_search import register_vector_search_tool
from .property_extraction import register_property_extraction_tools
from .annotations import register_annotation_tools
from .documents import register_document_tools
from .folders import register_folder_tools
from .custom_objects import register_custom_object_tools


# Define __all__ to specify what gets imported with "from tools import *"
__all__ = [
    "register_class_tools",
    "register_document_tools",
    "register_search_tools",
    "register_hold_tools",
    "register_vector_search_tool",
    "register_property_extraction_tools",
    "register_annotation_tools",
    "register_folder_tools",
    "register_custom_object_tools",
]
