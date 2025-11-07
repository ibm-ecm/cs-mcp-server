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
Tools module for MCP servers.

This module exports all tool registration functions from the tools directory.
"""

# Import all registration functions to make them available when importing from this package
from .classes import register_class_tools
from .search import register_search_tools
from .mcp_manage_hold import register_legalhold
from .vector_search import register_vector_search_tool
from .documents import register_document_tools


# Define __all__ to specify what gets imported with "from tools import *"
__all__ = [
    "register_class_tools",
    "register_document_tools",
    "register_search_tools",
    "register_legalhold",
    "register_vector_search_tool",
]
