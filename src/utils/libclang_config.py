"""
Unified libclang configuration utility
Handles libclang library discovery and configuration across the project
"""

import os
import clang.cindex
from pathlib import Path
from typing import Optional


class LibclangConfig:
    """Singleton class for libclang configuration"""
    
    _configured = False
    
    @classmethod
    def configure(cls, libclang_path: Optional[str] = None) -> bool:
        """
        Configure libclang with automatic discovery or specified path
        
        Args:
            libclang_path: Optional explicit path to libclang library
            
        Returns:
            bool: True if configuration successful, False otherwise
        """
        if cls._configured:
            return True
            
        try:
            # Check if already configured
            if clang.cindex.Config.library_file:
                print(f"libclang already configured: {clang.cindex.Config.library_file}")
                cls._configured = True
                return True
                
            # Try explicit path first
            if libclang_path and os.path.exists(libclang_path):
                clang.cindex.Config.set_library_file(libclang_path)
                print(f"Set libclang library to: {libclang_path}")
                cls._configured = True
                return True
                
            # Try environment variable
            env_path = os.environ.get('LIBCLANG_PATH')
            if env_path and os.path.exists(env_path):
                clang.cindex.Config.set_library_file(env_path)
                print(f"Set libclang library from environment: {env_path}")
                cls._configured = True
                return True
                
            # Auto-discovery for common paths
            common_paths = [
                '/usr/lib/llvm-10/lib/libclang.so.1',
                '/usr/lib/x86_64-linux-gnu/libclang-10.so.1', 
                '/usr/lib/llvm-10/lib/libclang.so',
                '/usr/lib/llvm-14/lib/libclang.so.1',
                '/usr/lib/llvm-14/lib/libclang.so',
                '/usr/lib/llvm-16/lib/libclang.so.1',
                '/usr/lib/llvm-16/lib/libclang.so',
                '/usr/local/opt/llvm/lib/libclang.dylib',  # macOS Homebrew
                'C:\\Program Files\\LLVM\\bin\\libclang.dll',  # Windows
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    clang.cindex.Config.set_library_file(path)
                    print(f"Auto-discovered libclang at: {path}")
                    cls._configured = True
                    return True
            
            # Last resort: try library path discovery
            lib_path = clang.cindex.Config.library_path
            if lib_path:
                potential_paths = [
                    os.path.join(lib_path, 'libclang.so.1'),
                    os.path.join(lib_path, 'libclang.so'),
                    os.path.join(lib_path, 'libclang.dll'),
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        clang.cindex.Config.set_library_file(path)
                        print(f"Found libclang in library path: {path}")
                        cls._configured = True
                        return True
            
            print("Warning: Could not auto-discover libclang library")
            return False
            
        except Exception as e:
            print(f"Error configuring libclang: {e}")
            return False
    
    @classmethod
    def ensure_configured(cls) -> bool:
        """Ensure libclang is configured, auto-discover if not"""
        if not cls._configured:
            return cls.configure()
        return True
    
    @classmethod
    def get_status(cls) -> dict:
        """Get current configuration status"""
        return {
            'configured': cls._configured,
            'library_file': clang.cindex.Config.library_file if cls._configured else None,
            'library_path': clang.cindex.Config.library_path
        }


def configure_libclang(libclang_path: Optional[str] = None) -> bool:
    """
    Convenience function for one-time libclang configuration
    
    Usage:
        from src.utils.libclang_config import configure_libclang
        configure_libclang('/usr/lib/llvm-10/lib/libclang.so.1')
    """
    return LibclangConfig.configure(libclang_path)


def ensure_libclang_configured() -> bool:
    """
    Ensure libclang is configured before using clang functionality
    
    Usage:
        from src.utils.libclang_config import ensure_libclang_configured
        ensure_libclang_configured()
        # Now safe to use clang functionality
    """
    return LibclangConfig.ensure_configured()