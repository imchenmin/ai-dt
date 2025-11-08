"""Prompt templates for LLM test generation with language-specific variations"""

from typing import Dict, Any, List
import os
import re
from pathlib import Path

import json
from src.test_generation.models import PromptContext
from src.utils.prompt_template_loader import PromptTemplateLoader

class PromptTemplates:
    """Templates for generating high-quality test generation prompts"""
    
    def __init__(self):
        """Initialize with template loader"""
        self.loader = PromptTemplateLoader()
    
    @staticmethod
    def get_system_prompt(language: str) -> str:
        """Get appropriate system prompt based on language"""
        loader = PromptTemplateLoader()
        return loader.get_system_prompt(language)
    
    @staticmethod
    def generate_test_prompt(compressed_context: Dict[str, Any] = None, existing_fixture_code: str = None, suite_name: str = None, existing_tests_context: Dict[str, Any] = None, prompt_context: PromptContext = None) -> str:
        """
        Generate comprehensive test generation prompt with a structured approach.
        
        Args:
            compressed_context: 压缩后的上下文信息（向后兼容）
            existing_fixture_code: 现有的fixture代码
            suite_name: 测试套件名称
            existing_tests_context: 现有测试上下文
            prompt_context: 结构化的提示词上下文对象（推荐使用）
        
        Returns:
            str: 生成的提示词
        """
        # 支持新旧两种调用方式
        if prompt_context is not None:
            # 使用新的结构化数据模型
            ctx = prompt_context
        else:
            # 向后兼容：从字典创建PromptContext对象
            ctx = PromptContext.from_compressed_context(
                compressed_context, existing_fixture_code, suite_name, existing_tests_context
            )
        
        # 使用新的模板加载器
        loader = PromptTemplateLoader()
        return PromptTemplates._generate_prompt_from_template(loader, ctx)
    
    @staticmethod
    def _generate_prompt_from_template(loader: PromptTemplateLoader, ctx: PromptContext) -> str:
        """Generate prompt using Jinja2 template system
        
        Args:
            loader: Template loader instance
            ctx: Prompt context with all necessary information
            
        Returns:
            Generated prompt string
        """
        language = ctx.target_function.language.value
        
        # Get appropriate Jinja2 template for language
        template_name = loader.get_template_for_language(language)
        
        # Prepare context for Jinja2 template
        jinja_context = PromptTemplates._prepare_jinja2_context(ctx)
        
        # Render template
        return loader.render_template(template_name, jinja_context)
    
    @staticmethod
    def _prepare_jinja2_context(ctx: PromptContext) -> Dict[str, Any]:
        """Prepare context dictionary for Jinja2 template rendering
        
        Args:
            ctx: Prompt context
            
        Returns:
            Dictionary containing all variables needed by Jinja2 templates
        """
        target = ctx.target_function
        deps = ctx.dependencies
        comp = ctx.compilation_info
        
        # Get filename for test class naming
        full_path = target.location
        clean_path = re.sub(r':\d+$', '', full_path)
        filename = Path(clean_path).stem
        
        # Prepare comprehensive context for Jinja2 templates
        context = {
            # Function information (matching template variables)
            'target_function_name': target.name,
            'target_location': target.location,
            'function_signature': target.signature,
            'function_body': target.body,
            'filename': filename,
            
            # Language information
            'language': target.language.value,
            'language_display': target.language.display_name,
            
            # Dependencies (matching template variables)
            'dependency_definitions': deps.dependency_definitions if deps else [],
            'macro_definitions': deps.macro_definitions if deps else [],
            'called_functions': deps.called_functions if deps else [],
            
            # Existing tests context - extract test code from ExistingTestsContext
            'existing_tests': PromptTemplates._extract_existing_tests(ctx.existing_tests_context),
            'existing_fixture_code': ctx.existing_fixture_code,
            'suite_name': ctx.suite_name,
            
            # Compilation information
            'include_paths': comp.include_paths if comp else [],
            'compiler_flags': comp.compiler_flags if comp else [],
            'defines': comp.defines if comp else [],
            
            # Additional context
            'has_external_dependencies': ctx.has_external_dependencies,
            'needs_mocking': ctx.has_external_dependencies
        }
        
        # Generate mock_guidance by rendering the mock_guidance.j2 template
        mock_guidance = PromptTemplates._generate_mock_guidance(ctx)
        if mock_guidance:
            context['mock_guidance'] = mock_guidance
        
        return context
    
    @staticmethod
    def _generate_mock_guidance(ctx: PromptContext) -> str:
        """Generate mock guidance by rendering the mock_guidance.j2 template

        Args:
            ctx: Prompt context

        Returns:
            Rendered mock guidance string or empty string if no guidance needed
        """
        try:
            loader = PromptTemplateLoader()

            # Prepare context for mock_guidance template
            # Convert target_function to dict format for template compatibility
            target_function_dict = {
                'name': ctx.target_function.name,
                'signature': ctx.target_function.signature,
                'return_type': ctx.target_function.return_type,
                'parameters': ctx.target_function.parameters,
                'body': ctx.target_function.body,
                'location': ctx.target_function.location,
                'language': ctx.target_function.language.value if hasattr(ctx.target_function.language, 'value') else ctx.target_function.language,
                'is_static': ctx.target_function.is_static,
                'access_specifier': ctx.target_function.access_specifier
            }

            # Convert dependencies to dict format
            dependencies_dict = {
                'called_functions': [{
                    'name': func.name,
                    'declaration': func.declaration,
                    'is_mockable': func.is_mockable,
                    'location': func.location
                } for func in ctx.dependencies.called_functions],
                'macros': ctx.dependencies.macros,
                'macro_definitions': [{
                    'name': macro.name,
                    'definition': macro.definition
                } for macro in ctx.dependencies.macro_definitions],
                'data_structures': ctx.dependencies.data_structures,
                'dependency_definitions': ctx.dependencies.dependency_definitions
            }

            mock_context = {
                'target_function': target_function_dict,
                'dependencies': dependencies_dict
            }

            # Render the mock_guidance.j2 template
            return loader.render_template('base/sections/mock_guidance.j2', mock_context)
        except Exception as e:
            # If template rendering fails, return empty string
            print(f"Warning: Failed to render mock_guidance template: {e}")
            return ""
    
    @staticmethod
    def _extract_existing_tests(existing_tests_context) -> List[str]:
        """Extract test code strings from ExistingTestsContext object
        
        Args:
            existing_tests_context: ExistingTestsContext object or None
            
        Returns:
            List of test code strings
        """
        if not existing_tests_context:
            return []
        
        test_codes = []
        
        # Extract test function codes
        if hasattr(existing_tests_context, 'existing_test_functions'):
            for test_func in existing_tests_context.existing_test_functions:
                if hasattr(test_func, 'code') and test_func.code:
                    test_codes.append(test_func.code)
        
        # Extract test class definitions
        if hasattr(existing_tests_context, 'existing_test_classes'):
            for test_class in existing_tests_context.existing_test_classes:
                if hasattr(test_class, 'definition') and test_class.definition:
                    test_codes.append(test_class.definition)
        
        return test_codes
    
