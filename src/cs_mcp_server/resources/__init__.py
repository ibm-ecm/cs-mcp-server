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
Resources module for MCP servers.

This module exports all resource registration functions from the resources directory.
Resources provide read-only access to data and content, complementing the tools
which perform operations and mutations.
"""

# Import all registration functions to make them available when importing from this package
from .dynamic_resources import register_dynamic_resources


__all__ = [
    "register_dynamic_resources",
]
