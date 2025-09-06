"""Prompt template loader with placeholder validation and multi-language support"""

import os
import json
import re
import yaml
from typing import Dict, Any, Set, List, Optional
from pathlib import Path
from src.test_generation.models import PromptContext

try:
    from jinja2 import Environment, FileSystemLoader, Template
    JINJA2_AVAILABLE = True
except ImportError:
    Environment = None
    FileSystemLoader = None
    Template = None
    JINJA2_AVAILABLE = False


class TemplateValidationError(Exception):
    """Exception raised when template validation fails"""
    pass


class PromptTemplateLoader:
    """Loads and validates prompt templates with Jinja2 support"""
    
    def __init__(self, templates_dir: str = None, config_path: str = None):
        """Initialize the template loader
        
        Args:
            templates_dir: Directory containing template files. Defaults to project templates/prompts
            config_path: Path to template configuration file
        """
        if templates_dir is None:
            # Get project root directory
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(os.path.dirname(current_dir))
            templates_dir = os.path.join(project_root, "templates", "prompts")
        
        self.templates_dir = Path(templates_dir)
        self.jinja2_dir = self.templates_dir / "jinja2"
        self._template_cache: Dict[str, str] = {}
        self._system_prompts: Dict[str, str] = {}
        self._config: Dict[str, Any] = {}
        
        # Initialize Jinja2 environment
        self.jinja_env: Optional[Environment] = None
        if self.jinja2_dir.exists():
            self._setup_jinja_environment()
        
        # Load configuration and system prompts
        self._load_template_config(config_path)
        self._load_system_prompts()
    
    def _setup_jinja_environment(self):
        """Setup Jinja2 environment for template rendering"""
        if not JINJA2_AVAILABLE:
            raise ImportError("Jinja2 is required for template rendering but not installed")
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.jinja2_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
    
    def _load_template_config(self, config_path: str = None):
        """Load template configuration from YAML file"""
        if config_path is None:
            # Try default config locations
            project_root = self.templates_dir.parent.parent
            config_candidates = [
                project_root / "config" / "template_config.yaml",
                project_root / "config" / "template_config.yml",
                self.templates_dir / "config.yaml",
                self.templates_dir / "config.yml"
            ]
            
            for candidate in config_candidates:
                if candidate.exists():
                    config_path = str(candidate)
                    break
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load template config from {config_path}: {e}")
                self._config = {}
        else:
            # Default configuration
            self._config = {
                'default_template_set': 'base',
                'template_sets': {
                    'base': {
                        'base_template': 'base/test_generation.j2',
                        'language_overrides': {
                            'c': 'c/test_generation.j2',
                            'c++': 'cpp/test_generation.j2'
                        }
                    }
                }
            }
    
    def _load_system_prompts(self):
        """Load system prompts from JSON file"""
        system_prompts_file = self.templates_dir / "system_prompts.json"
        if system_prompts_file.exists():
            with open(system_prompts_file, 'r', encoding='utf-8') as f:
                self._system_prompts = json.load(f)
        else:
            # Fallback to default prompts
            self._system_prompts = {
                'c': "你是一个专业的C语言单元测试工程师，专门生成Google Test + MockCpp测试用例。",
                'c++': "你是一个专业的C++单元测试工程师，专门生成Google Test + MockCpp测试用例。",
                'java': "你是一个专业的Java单元测试工程师，专门生成JUnit 5 + Mockito测试用例。",
                'default': "你是一个专业的单元测试工程师，专门生成高质量的单元测试用例。"
            }
    
    def get_system_prompt(self, language: str) -> str:
        """Get system prompt for specified language
        
        Args:
            language: Programming language (c, c++, java, etc.)
            
        Returns:
            System prompt string
        """
        return self._system_prompts.get(language, self._system_prompts['default'])
    
    def load_template(self, template_name: str) -> str:
        """Load template from file with caching
        
        Args:
            template_name: Name of template file (without .txt extension)
            
        Returns:
            Template content as string
            
        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        template_file = self.templates_dir / f"{template_name}.txt"
        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")
        
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self._template_cache[template_name] = content
        return content
    
    def extract_placeholders(self, template: str) -> Set[str]:
        """Extract all placeholders from template
        
        Args:
            template: Template string
            
        Returns:
            Set of placeholder names (without braces)
        """
        # Find all {placeholder} patterns
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, template)
        return set(matches)
    
    def validate_placeholders(self, template: str, provided_vars: Dict[str, Any]) -> List[str]:
        """Validate that all placeholders have corresponding variables
        
        Args:
            template: Template string
            provided_vars: Dictionary of variables to substitute
            
        Returns:
            List of missing placeholder names
        """
        required_placeholders = self.extract_placeholders(template)
        provided_keys = set(provided_vars.keys())
        missing = required_placeholders - provided_keys
        return list(missing)
    
    def validate_template_syntax(self, template: str) -> List[str]:
        """Validate template syntax for common issues
        
        Args:
            template: Template string
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check for unmatched braces
        open_braces = template.count('{')
        close_braces = template.count('}')
        if open_braces != close_braces:
            errors.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
        
        # Check for nested braces (not supported)
        nested_pattern = r'\{[^}]*\{[^}]*\}[^}]*\}'
        if re.search(nested_pattern, template):
            errors.append("Nested braces are not supported")
        
        # Check for empty placeholders
        empty_pattern = r'\{\s*\}'
        if re.search(empty_pattern, template):
            errors.append("Empty placeholders found")
        
        return errors
    
    def substitute_template(self, template: str, variables: Dict[str, Any], strict: bool = True) -> str:
        """Substitute variables in template
        
        Args:
            template: Template string
            variables: Dictionary of variables to substitute
            strict: If True, raise error for missing variables
            
        Returns:
            Template with substituted variables
            
        Raises:
            TemplateValidationError: If strict=True and variables are missing
        """
        # Validate template syntax first
        syntax_errors = self.validate_template_syntax(template)
        if syntax_errors:
            raise TemplateValidationError(f"Template syntax errors: {'; '.join(syntax_errors)}")
        
        # Check for missing variables
        missing_vars = self.validate_placeholders(template, variables)
        if missing_vars and strict:
            raise TemplateValidationError(f"Missing template variables: {', '.join(missing_vars)}")
        
        # Perform substitution
        if not strict:
            # In non-strict mode, only substitute available variables
            import string
            class SafeFormatter(string.Formatter):
                def get_value(self, key, args, kwargs):
                    if isinstance(key, str):
                        try:
                            return kwargs[key]
                        except KeyError:
                            return '{' + key + '}'
                    else:
                        return string.Formatter.get_value(key, args, kwargs)
            
            formatter = SafeFormatter()
            return formatter.format(template, **variables)
        else:
            # In strict mode, all variables must be provided
            try:
                return template.format(**variables)
            except KeyError as e:
                raise TemplateValidationError(f"Template substitution failed: {e}")
            except ValueError as e:
                raise TemplateValidationError(f"Template format error: {e}")
    
    def validate_variables(self, template: str, variables: Dict[str, Any], strict: bool = True) -> None:
        """Validate variables for template substitution
        
        Args:
            template: Template string
            variables: Dictionary of variables to validate
            strict: If True, raise error for missing variables
            
        Raises:
            TemplateValidationError: If strict=True and variables are missing
        """
        # Validate template syntax first
        syntax_errors = self.validate_template_syntax(template)
        if syntax_errors:
            raise TemplateValidationError(f"Template syntax errors: {'; '.join(syntax_errors)}")
        
        # Check for missing variables
        missing_vars = self.validate_placeholders(template, variables)
        if missing_vars and strict:
            raise TemplateValidationError(f"Missing required variables: {', '.join(missing_vars)}")
    
    def substitute_variables(self, template: str, variables: Dict[str, Any], strict: bool = True) -> str:
        """Substitute variables in template (alias for substitute_template)
        
        Args:
            template: Template string
            variables: Dictionary of variables to substitute
            strict: If True, raise error for missing variables
            
        Returns:
            Template with substituted variables
        """
        return self.substitute_template(template, variables, strict)
    
    def load_and_substitute(self, template_name: str, variables: Dict[str, Any], strict: bool = True) -> str:
        """Load template and substitute variables in one step
        
        Args:
            template_name: Name of template file
            variables: Dictionary of variables to substitute
            strict: If True, raise error for missing variables
            
        Returns:
            Processed template string
        """
        template = self.load_template(template_name)
        return self.substitute_template(template, variables, strict)
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names
        
        Returns:
            List of template names (without .txt extension)
        """
        if not self.templates_dir.exists():
            return []
        
        templates = []
        for file_path in self.templates_dir.glob("*.txt"):
            templates.append(file_path.stem)
        
        return templates
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a Jinja2 template with the given context
        
        Args:
            template_name: Name of the template file (e.g., 'c/test_generation.j2')
            context: Dictionary containing template variables
            
        Returns:
            Rendered template content
            
        Raises:
            TemplateValidationError: If template rendering fails
        """
        if not self.jinja_env:
            raise TemplateValidationError("Jinja2 environment not initialized")
        
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise TemplateValidationError(f"Failed to render template '{template_name}': {str(e)}")
    
    def get_template_for_language(self, language: str, template_set: str = None) -> str:
        """Get the appropriate template name for a given language
        
        Args:
            language: Programming language (e.g., 'c', 'c++', 'java')
            template_set: Template set to use (defaults to configured default)
            
        Returns:
            Template name/path for the language
        """
        template_set = template_set or self._config.get('default_template_set', 'base')
        templates = self._config.get('template_sets', {}).get(template_set, {})
        
        # Check for language-specific override
        language_overrides = templates.get('language_overrides', {})
        if language.lower() in language_overrides:
            return language_overrides[language.lower()]
        
        # Fall back to base template
        return templates.get('base_template', 'base/test_generation.j2')
    
    def has_jinja2_support(self) -> bool:
        """Check if Jinja2 templates are available and supported"""
        return self.jinja_env is not None and JINJA2_AVAILABLE
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get information about a template
        
        Args:
            template_name: Name of template file
            
        Returns:
            Dictionary with template information
        """
        try:
            template = self.load_template(template_name)
            placeholders = self.extract_placeholders(template)
            syntax_errors = self.validate_template_syntax(template)
            
            return {
                'name': template_name,
                'placeholders': list(placeholders),
                'placeholder_count': len(placeholders),
                'syntax_errors': syntax_errors,
                'is_valid': len(syntax_errors) == 0,
                'size_bytes': len(template.encode('utf-8'))
            }
        except FileNotFoundError:
            return {
                'name': template_name,
                'error': 'Template file not found'
            }