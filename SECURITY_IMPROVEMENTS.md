# Security Improvements for BGP Creator

## Summary
Comprehensive security validation and sanitization has been added to BGP Creator to prevent common web vulnerabilities including XSS, path traversal, and injection attacks.

## Changes Made

### 1. core/validators.py
- **Added new validation functions:**
  - `validate_safe_path()` - Prevents directory traversal attacks
  - `sanitize_html_content()` - Escapes HTML to prevent XSS
  - `validate_url_strict()` - Validates URLs against dangerous schemes
  - `validate_image_path()` - Validates image paths with security checks
  - `sanitize_filename()` - Sanitizes filenames for safe file operations
  - `validate_config()` - Enhanced config validation with security checks

- **Security features implemented:**
  - Path traversal prevention (blocks ../, absolute paths when not expected)
  - XSS prevention (HTML escaping, dangerous URL scheme blocking)
  - Null byte injection prevention
  - File extension validation for images
  - Rate limiting documentation and recommendations

### 2. core/site_loader.py
- **Enhanced `validate_site_name()` function:**
  - Added length validation (max 253 chars per RFC)
  - Expanded dangerous character checks
  - Added domain label validation (1-63 chars per label)
  - Added null byte and control character prevention

- **Added new security functions:**
  - `validate_file_path_security()` - Validates file paths are within base directory
  - `sanitize_path_component()` - Removes dangerous characters from path components

- **Enhanced `get_site_output_dir()` function:**
  - Added system directory protection
  - Path sanitization for custom output directories
  - Validation against writing to system directories

### 3. core/game_manager.py
- **Added security methods:**
  - `_sanitize_game_metadata()` - Sanitizes all metadata fields
  - `_validate_game_url()` - Validates game URLs against XSS
  - `_validate_image_path()` - Validates image paths for safety

- **Enhanced existing methods:**
  - `_extract_title()` - Now escapes HTML in titles
  - `_extract_embed_url()` - Validates URLs before returning
  - `_extract_hero_image()` - Validates image paths before returning
  - `_extract_metadata()` - Sanitizes metadata after parsing

- **Security features:**
  - HTML escaping for text fields (title, description, etc.)
  - URL validation for embed/link fields
  - Image path validation
  - XSS pattern detection

### 4. core/generator_refactored.py
- **Enhanced initialization with validation:**
  - Site name validation at entry point
  - Configuration validation with error reporting
  - Template directory validation and sanitization
  - Output directory validation
  - Path security checks

- **Security features:**
  - Input validation at all entry points
  - Sanitization of user-provided paths
  - Security error reporting
  - Backward compatibility maintained

## Security Features Implemented

### XSS Prevention
- HTML special character escaping in all user-provided text
- Dangerous URL scheme blocking (javascript:, data:, vbscript:)
- Pattern detection for inline event handlers
- Content sanitization in templates (via Jinja2 autoescape)

### Path Traversal Prevention
- Validation against ../ sequences
- Absolute path restrictions where appropriate
- Path normalization and resolution
- Base directory containment checks

### Injection Prevention
- Null byte filtering
- Control character removal
- File extension validation
- Filename sanitization

### Rate Limiting Considerations
Rate limiting should be implemented at:
1. Web server level (nginx/Apache)
2. Application entry points (main.py)
3. Resource-intensive operations
4. API endpoints (if exposed)

## Backward Compatibility
All security improvements maintain backward compatibility:
- Existing configurations continue to work
- Valid inputs are processed normally
- Only malicious or dangerous inputs are blocked
- Warning messages for sanitized content

## Testing
The security improvements have been tested and verified:
- Generator initializes successfully with validation
- Site generation completes without errors
- Web server serves content correctly
- All existing functionality preserved

## Recommendations for Production
1. Implement rate limiting at the web server level
2. Use HTTPS for all production deployments
3. Implement Content Security Policy (CSP) headers
4. Regular security audits and updates
5. Monitor for suspicious patterns in logs