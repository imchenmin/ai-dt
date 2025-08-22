# TODO: C++ Class Method Analysis Improvements

## Current Status
C++ class method analysis is partially working but needs enhancement. The current implementation correctly identifies:
- ✅ Free functions (non-member functions)
- ✅ Public methods (basic detection)
- ✅ Function signatures (return types, parameters)

## Issues to Address

### 1. C++ Class Method Recognition
- **Problem**: Class methods are not being properly distinguished from free functions
- **Solution**: Enhance `clang_analyzer.py` to better handle C++ class hierarchy

### 2. Method Deduplication  
- **Problem**: Methods appear multiple times across translation units
- **Solution**: Implement function signature-based deduplication

### 3. Access Specifier Handling
- **Problem**: Private/protected methods need special handling for symbol hijacking
- **Solution**: Improve access specifier detection and testability logic

### 4. Template Method Support
- **Problem**: Template methods and classes are not properly handled
- **Solution**: Add template parameter extraction and specialization support

## Implementation Plan

### Phase 1: Basic C++ Class Support
```python
# In clang_analyzer.py
def _get_function_info(self, cursor, file_path: str):
    # Add class context detection
    if cursor.kind == clang.cindex.CursorKind.CXX_METHOD:
        # Extract class information
        class_cursor = cursor.semantic_parent
        if class_cursor and class_cursor.kind == clang.cindex.CursorKind.CLASS_DECL:
            function_info['class_name'] = class_cursor.spelling
            function_info['is_method'] = True
```

### Phase 2: Advanced C++ Features
- Constructor/destructor detection
- Operator overload identification  
- Template instantiation tracking
- Namespace context preservation

### Phase 3: Symbol Hijacking for Private Methods
- Develop strategy for testing private methods
- Implement function interception mechanism
- Generate appropriate MockCpp code for private method testing

## Test Cases Needed
1. Simple class with public/private methods
2. Template classes and methods
3. Inheritance hierarchy methods
4. Operator overload functions
5. Namespaced classes and methods

## Priority: Medium
This improvement is important but not blocking for initial MVP. Can be implemented after core test generation is working.