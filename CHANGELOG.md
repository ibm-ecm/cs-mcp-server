# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2026-02-24

### Added
- Added AI Document Insight Server (`ai-document-insight-cs-mcp-server`) with 4 specialized tools:
  - `document_smart_search`: Hybrid search combining vector (semantic) search with metadata filtering using Content Assistant API
  - `document_quick_summary`: AI-powered document summarization for one or more documents
  - `document_compare_insights`: Compare two documents to identify similarities, differences, and version changes
  - `document_qa_global`: Answer natural language questions by scanning the entire document repository
- Enhanced `document_search` tool in Core Server with improved content-based search using full-text CBR search
  - Can combine content-based search with property filters for precise document discovery
  - Returns only released versions of documents
  - Automatically escapes special characters in search terms

### Changed
- **IMPORTANT**: Document search workflow updated - use `document_search` tool instead of `repository_object_search` for document searches
  - `document_search` provides specialized document search with content-based and metadata filtering
  - `repository_object_search` remains available for searching other repository objects (folders, custom objects, etc.)

### Removed
- Removed get annotation and custom object tools from Core Server (low usage)

### Fixed
- Fixed GraphQL client async wrapper execution issues
- Fixed import statement errors in document tools
- Improved error message response if text extract does not exist.

## [1.0.2] - 2026-01-30

### Added
- Added `file_document` tool to file documents into folders
- Added Legal Hold Server (`legal-hold-cs-mcp-server`) with 6 tools for legal compliance management:
  - `create_hold`: Create new legal holds
  - `delete_hold`: Remove legal holds
  - `add_object_to_hold`: Place objects under legal hold
  - `delete_object_from_hold`: Remove objects from legal hold
  - `get_held_objects_for_hold`: List objects under a specific hold
  - `get_holds_by_name`: Search for legal holds by name
- Added Property Extraction and Classification Server (`property-extraction-and-classification-cs-mcp-server`) with 2 tools:
  - `property_extraction`: Extract document properties and text content for AI-based analysis
  - `list_all_classes`: List all available classes for document classification workflows
- Added `get_annotation` tool to retrieve specific annotations by ID
- Added `get_custom_object` tool to retrieve custom objects from the repository

## [1.0.1] - 2025-12-12

### Fixed
- Fixed download async requests not disabling SSL verification when `SSL_ENABLED` is set to `false`

## [1.0.0] - 2025-12-05

### Added
- Initial GA (General Availability) release
- IBM Content Services MCP Server implementation
- GraphQL client for Content Services integration
- Document management tools (create, update, delete, download)
- Folder management tools (create, update, delete, list)
- Search capabilities (basic)
- Class and annotation management
- SSL/TLS support with configurable verification

[1.0.3]: https://github.com/ibm-ecm/ibm-content-services-mcp-server/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/ibm-ecm/ibm-content-services-mcp-server/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/ibm-ecm/ibm-content-services-mcp-server/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/ibm-ecm/ibm-content-services-mcp-server/releases/tag/v1.0.0