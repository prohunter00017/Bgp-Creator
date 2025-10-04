"""
Error Recovery Module for BGP Creator

Provides standardized error handling, recovery strategies, and graceful degradation
for the static site generator. This module ensures consistent error handling across
all components with proper fallbacks and user-friendly error messages.
"""

import os
import json
import traceback
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from core.performance_logger import log_error, log_warn, log_info


class RecoveryContext:
    """Context manager for error recovery with automatic fallback strategies."""
    
    def __init__(self, operation_name: str, component: str, fallback_value: Any = None,
                 recovery_strategy: Optional[Callable] = None, critical: bool = False):
        """
        Initialize recovery context.
        
        Args:
            operation_name: Name of the operation being performed
            component: Component name for logging
            fallback_value: Default value to return on error
            recovery_strategy: Optional function to call for recovery
            critical: If True, raises exception after logging
        """
        self.operation_name = operation_name
        self.component = component
        self.fallback_value = fallback_value
        self.recovery_strategy = recovery_strategy
        self.critical = critical
        self.errors = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return True
            
        # Log the error with specific type information
        error_msg = f"{self.operation_name} failed: {exc_type.__name__}: {str(exc_value)}"
        log_error(self.component, error_msg, "❌")
        
        # Store error for later analysis
        self.errors.append({
            'operation': self.operation_name,
            'error_type': exc_type.__name__,
            'error_msg': str(exc_value),
            'traceback': traceback.format_exc()
        })
        
        # Try recovery strategy if provided
        if self.recovery_strategy:
            try:
                log_info(self.component, f"Attempting recovery for {self.operation_name}", "🔧")
                self.recovery_strategy()
                log_info(self.component, f"Recovery successful for {self.operation_name}", "✅")
            except Exception as recovery_error:
                log_error(self.component, f"Recovery failed: {recovery_error}", "❌")
        
        # Re-raise if critical
        if self.critical:
            return False
        
        # Suppress exception and continue
        return True


class ErrorRecovery:
    """Main error recovery handler with built-in recovery strategies."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.error_log_path = os.path.join(output_dir, "build_errors.json")
        self.recovery_stats = {
            'total_errors': 0,
            'recovered': 0,
            'failed': 0,
            'critical': 0
        }
    
    def safe_file_operation(self, operation: Callable, filepath: str, 
                           fallback_content: str = "", component: str = "FileOp") -> bool:
        """
        Safely perform file operations with automatic recovery.
        
        Args:
            operation: File operation to perform
            filepath: Path to file
            fallback_content: Content to write if operation fails
            component: Component name for logging
            
        Returns:
            True if operation succeeded (or recovered), False otherwise
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                operation()
                return True
            except PermissionError as e:
                retry_count += 1
                log_warn(component, f"Permission denied on {filepath}, attempt {retry_count}/{max_retries}", "⚠️")
                
                # Try to fix permissions
                try:
                    os.chmod(filepath, 0o644)
                except:
                    pass
                    
                if retry_count >= max_retries:
                    self.recovery_stats['failed'] += 1
                    # Create fallback if possible
                    if fallback_content:
                        try:
                            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                            with open(filepath + ".fallback", 'w') as f:
                                f.write(fallback_content)
                            log_info(component, f"Created fallback file: {filepath}.fallback", "📝")
                            self.recovery_stats['recovered'] += 1
                        except:
                            pass
                    return False
                    
            except (OSError, IOError) as e:
                self.recovery_stats['total_errors'] += 1
                log_error(component, f"File operation failed on {filepath}: {e}", "❌")
                
                # Try to create parent directory
                try:
                    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
                    retry_count += 1
                    if retry_count < max_retries:
                        continue
                except:
                    pass
                    
                self.recovery_stats['failed'] += 1
                return False
                
            except Exception as e:
                self.recovery_stats['total_errors'] += 1
                log_error(component, f"Unexpected error on {filepath}: {type(e).__name__}: {e}", "❌")
                self.recovery_stats['failed'] += 1
                return False
        
        return False
    
    def safe_template_render(self, template_func: Callable, fallback_html: str,
                            component: str = "Template") -> str:
        """
        Safely render template with fallback HTML.
        
        Args:
            template_func: Template rendering function
            fallback_html: Fallback HTML if rendering fails
            component: Component name for logging
            
        Returns:
            Rendered HTML or fallback
        """
        try:
            return template_func()
        except Exception as e:
            self.recovery_stats['total_errors'] += 1
            log_error(component, f"Template render failed: {type(e).__name__}: {e}", "❌")
            log_info(component, "Using fallback HTML", "🔄")
            self.recovery_stats['recovered'] += 1
            return fallback_html
    
    def safe_json_load(self, filepath: str, default: Optional[Dict] = None, 
                      component: str = "JSON") -> Dict:
        """
        Safely load JSON file with fallback to default.
        
        Args:
            filepath: Path to JSON file
            default: Default value if load fails
            component: Component name for logging
            
        Returns:
            Loaded JSON data or default
        """
        if default is None:
            default = {}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            log_warn(component, f"JSON file not found: {filepath}, using default", "⚠️")
            self.recovery_stats['recovered'] += 1
            return default
        except json.JSONDecodeError as e:
            self.recovery_stats['total_errors'] += 1
            log_error(component, f"Invalid JSON in {filepath}: {e}", "❌")
            
            # Try to create backup and use default
            try:
                import shutil
                backup_path = f"{filepath}.backup"
                shutil.copy2(filepath, backup_path)
                log_info(component, f"Created backup: {backup_path}", "💾")
            except:
                pass
                
            self.recovery_stats['recovered'] += 1
            return default
        except Exception as e:
            self.recovery_stats['total_errors'] += 1
            log_error(component, f"Failed to load {filepath}: {type(e).__name__}: {e}", "❌")
            self.recovery_stats['failed'] += 1
            return default
    
    def log_recovery_summary(self):
        """Log a summary of error recovery statistics."""
        if self.recovery_stats['total_errors'] > 0:
            log_info("ErrorRecovery", "=== Error Recovery Summary ===", "📊")
            log_info("ErrorRecovery", f"Total errors: {self.recovery_stats['total_errors']}", "📈")
            log_info("ErrorRecovery", f"Successfully recovered: {self.recovery_stats['recovered']}", "✅")
            log_info("ErrorRecovery", f"Failed to recover: {self.recovery_stats['failed']}", "❌")
            
            if self.recovery_stats['critical'] > 0:
                log_warn("ErrorRecovery", f"Critical errors: {self.recovery_stats['critical']}", "⚠️")
            
            # Save error log
            try:
                os.makedirs(os.path.dirname(self.error_log_path), exist_ok=True)
                with open(self.error_log_path, 'w') as f:
                    json.dump(self.recovery_stats, f, indent=2)
                log_info("ErrorRecovery", f"Error log saved to: {self.error_log_path}", "💾")
            except:
                pass
    
    def create_fallback_page(self, title: str, message: str) -> str:
        """
        Create a simple fallback HTML page.
        
        Args:
            title: Page title
            message: Error message to display
            
        Returns:
            Fallback HTML content
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: system-ui, -apple-system, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            max-width: 600px;
        }}
        h1 {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        .btn {{
            display: inline-block;
            margin-top: 2rem;
            padding: 12px 24px;
            background: white;
            color: #667eea;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>{message}</p>
        <a href="/" class="btn">Go Home</a>
    </div>
</body>
</html>"""


# Global instance for easy access
recovery_handler = None

def get_recovery_handler(output_dir: str = "output") -> ErrorRecovery:
    """Get or create the global error recovery handler."""
    global recovery_handler
    if recovery_handler is None:
        recovery_handler = ErrorRecovery(output_dir)
    return recovery_handler