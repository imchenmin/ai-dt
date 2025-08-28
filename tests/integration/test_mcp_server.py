"""
Integration tests for AI-DT MCP Server
"""

import pytest
import json
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.mcp_server import AIDTMCPHandler
from src.analyzer.clang_analyzer import ClangAnalyzer
from src.utils.context_compressor import ContextCompressor


class TestMCPIntegration:
    """Integration tests for MCP server functionality"""
    
    @pytest.fixture
    def mcp_handler(self):
        """Create MCP handler instance"""
        return AIDTMCPHandler()
    
    # @pytest.fixture
    # def mcp_protocol(self):
    #     """Create MCP protocol instance"""
    #     return AIDTMCPProtocol()
    
    @pytest.fixture
    def test_c_file(self):
        """Create a temporary test C file"""
        test_code = """
#include <stdio.h>
#include <stdlib.h>

// Simple test function
int add_numbers(int a, int b) {
    return a + b;
}

// Static helper function
static int multiply_numbers(int x, int y) {
    return x * y;
}

// Function using malloc
int* create_int_array(int size) {
    if (size <= 0) return NULL;
    return (int*)malloc(size * sizeof(int));
}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write(test_code)
            temp_file = f.name
        
        yield temp_file
        
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    def test_mcp_handler_initialization(self):
        """Test MCP handler initialization"""
        handler = AIDTMCPHandler()
        
        assert hasattr(handler, 'analyzer')
        assert hasattr(handler, 'parser')
        assert hasattr(handler, 'compressor')
        assert isinstance(handler.analyzer, ClangAnalyzer)
        assert isinstance(handler.compressor, ContextCompressor)
    
    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_handler):
        """Test listing available MCP tools"""
        tools = await mcp_handler.handle_list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) == 3
        
        tool_names = [tool['name'] for tool in tools]
        assert 'generate_test_prompt' in tool_names
        assert 'analyze_function_dependencies' in tool_names
        assert 'get_function_signature' in tool_names
        
        # Check tool schemas
        for tool in tools:
            assert 'name' in tool
            assert 'description' in tool
            assert 'inputSchema' in tool
            assert 'properties' in tool['inputSchema']
            assert 'required' in tool['inputSchema']
    
    @pytest.mark.asyncio
    async def test_get_function_signature_valid(self, mcp_handler, test_c_file):
        """Test getting function signature from valid file"""
        params = {
            'file_path': test_c_file,
            'function_name': 'add_numbers'
        }
        
        result = await mcp_handler.handle_get_signature(params)
        
        assert 'signature' in result
        assert 'return_type' in result
        assert 'parameters' in result
        assert 'location' in result
        assert 'language' in result
        
        assert result['return_type'] == 'int'
        assert 'add_numbers' in result['signature']
        assert len(result['parameters']) == 2
    
    @pytest.mark.asyncio
    async def test_get_function_signature_invalid_function(self, mcp_handler, test_c_file):
        """Test getting signature for non-existent function"""
        params = {
            'file_path': test_c_file,
            'function_name': 'non_existent_function'
        }
        
        result = await mcp_handler.handle_get_signature(params)
        
        assert 'error' in result
        assert 'available_functions' in result
        assert isinstance(result['available_functions'], list)
    
    @pytest.mark.asyncio
    async def test_get_function_signature_invalid_file(self, mcp_handler):
        """Test getting signature from non-existent file"""
        params = {
            'file_path': '/non/existent/file.c',
            'function_name': 'some_function'
        }
        
        result = await mcp_handler.handle_get_signature(params)
        
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_analyze_dependencies_valid(self, mcp_handler, test_c_file):
        """Test analyzing function dependencies"""
        params = {
            'file_path': test_c_file,
            'function_name': 'create_int_array'
        }
        
        result = await mcp_handler.handle_analyze_dependencies(params)
        
        assert 'function' in result
        assert 'dependencies' in result
        assert 'called_functions' in result
        assert 'macros_used' in result
        assert 'data_structures' in result
        
        # Should return empty dependencies for now (simplified implementation)
        assert isinstance(result['called_functions'], list)
    
    @pytest.mark.asyncio
    async def test_generate_test_prompt_valid(self, mcp_handler, test_c_file):
        """Test generating test prompt for valid function"""
        params = {
            'file_path': test_c_file,
            'function_name': 'add_numbers',
            'project_root': os.path.dirname(test_c_file)
        }
        
        result = await mcp_handler.handle_generate_test_prompt(params)
        
        assert 'prompt' in result
        assert 'function_info' in result
        assert 'dependencies' in result
        assert 'language' in result
        
        # Check function info
        func_info = result['function_info']
        assert func_info['name'] == 'add_numbers'
        assert func_info['return_type'] == 'int'
        assert len(func_info['parameters']) == 2
        
        # Check prompt content
        prompt = result['prompt']
        assert 'add_numbers' in prompt
        assert 'Google Test' in prompt
        assert 'MockCpp' in prompt
    
    # @pytest.mark.asyncio
    # async def test_mcp_protocol_initialize(self, mcp_protocol):
    #     """Test MCP protocol initialization"""
    #     request = {
    #         'method': 'initialize',
    #         'params': {}
    #     }
    #     
    #     response = await mcp_protocol.handle_request(request)
    #     
    #     assert 'result' in response
    #     assert 'capabilities' in response['result']
    #     assert 'tools' in response['result']['capabilities']
    
    # @pytest.mark.asyncio
    # async def test_mcp_protocol_list_tools(self, mcp_protocol):
    #     """Test MCP protocol tools listing"""
    #     request = {
    #         'method': 'tools/list',
    #         'params': {}
    #     }
    #     
    #     response = await mcp_protocol.handle_request(request)
    #     
    #     assert 'result' in response
    #     assert isinstance(response['result'], list)
    #     assert len(response['result']) == 3
    
    # @pytest.mark.asyncio
    # async def test_mcp_protocol_tool_call_valid(self, mcp_protocol, test_c_file):
    #     """Test MCP protocol tool call with valid parameters"""
    #     request = {
    #         'method': 'tools/call',
    #         'params': {
    #             'name': 'get_function_signature',
    #             'arguments': {
    #                 'file_path': test_c_file,
    #                 'function_name': 'add_numbers'
    #             }
    #         }
    #     }
    #     
    #     response = await mcp_protocol.handle_request(request)
    #     
    #     assert 'result' in response
    #     assert 'signature' in response['result']
    
    # @pytest.mark.asyncio
    # async def test_mcp_protocol_tool_call_invalid(self, mcp_protocol):
    #     """Test MCP protocol tool call with invalid tool name"""
    #     request = {
    #         'method': 'tools/call',
    #         'params': {
    #             'name': 'invalid_tool',
    #             'arguments': {}
    #         }
    #     }
    #     
    #     response = await mcp_protocol.handle_request(request)
    #     
    #     assert 'error' in response
    #     assert response['error']['code'] == -32601
    
    # @pytest.mark.asyncio
    # async def test_mcp_protocol_shutdown(self, mcp_protocol):
    #     """Test MCP protocol shutdown"""
    #     request = {
    #         'method': 'shutdown',
    #         'params': {}
    #     }
    #     
    #     response = await mcp_protocol.handle_request(request)
    #     
    #     assert 'result' in response
    #     assert response['result'] is None
    
    # @pytest.mark.asyncio
    # async def test_mcp_protocol_method_not_found(self, mcp_protocol):
    #     """Test MCP protocol with unknown method"""
    #     request = {
    #         'method': 'unknown_method',
    #         'params': {}
    #     }
    #     
    #     response = await mcp_protocol.handle_request(request)
    #     
    #     assert 'error' in response
    #     assert response['error']['code'] == -32601


class TestMCPErrorHandling:
    """Test MCP server error handling"""
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_required_params(self):
        """Test error handling for missing required parameters"""
        handler = AIDTMCPHandler()
        
        # Missing file_path
        params = {'function_name': 'test'}
        result = await handler.handle_get_signature(params)
        assert 'error' in result
        
        # Missing function_name
        params = {'file_path': '/some/file.c'}
        result = await handler.handle_get_signature(params)
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_error_handling_file_permission_issues(self):
        """Test error handling for file permission issues"""
        handler = AIDTMCPHandler()
        
        # Create a file with no read permission
        with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
            f.write('int test() { return 0; }')
            temp_file = f.name
        
        try:
            # Remove read permission
            os.chmod(temp_file, 0o000)
            
            params = {
                'file_path': temp_file,
                'function_name': 'test'
            }
            
            result = await handler.handle_get_signature(params)
            assert 'error' in result
            
        finally:
            # Restore permission and cleanup
            os.chmod(temp_file, 0o644)
            os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])