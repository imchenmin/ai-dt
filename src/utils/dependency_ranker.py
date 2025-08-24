"""
Dependency ranking system for intelligent context compression
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import re


class DependencyType(Enum):
    """Types of dependencies with different importance levels"""
    CALLED_FUNCTION = 1
    DATA_STRUCTURE = 2
    MACRO = 3
    INCLUDE_DIRECTIVE = 4


class ImportanceLevel(Enum):
    """Importance levels for dependencies"""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


@dataclass
class RankedDependency:
    """A dependency with calculated importance score"""
    name: str
    type: DependencyType
    importance: ImportanceLevel
    score: float
    data: Any
    
    def __lt__(self, other):
        return self.score < other.score


class DependencyRanker:
    """Ranks dependencies by importance for intelligent compression"""
    
    # Weight factors for different importance criteria
    WEIGHTS = {
        'same_module': 2.0,
        'call_frequency': 1.5,
        'complexity': 1.2,
        'data_usage': 1.8,
        'macro_complexity': 1.1,
    }
    
    # Patterns for identifying critical dependencies
    CRITICAL_PATTERNS = [
        r'malloc', r'free', r'alloc', r'dealloc',
        r'create', r'destroy', r'init', r'cleanup',
        r'error', r'assert', r'check', r'validate'
    ]
    
    def __init__(self, target_function: Dict[str, Any]):
        self.target_function = target_function
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                 for pattern in self.CRITICAL_PATTERNS]
    
    def rank_called_functions(self, called_functions: List[Dict[str, Any]], 
                             all_functions: List[Dict[str, Any]]) -> List[RankedDependency]:
        """Rank called functions by importance"""
        ranked = []
        
        for func in called_functions:
            score = self._calculate_function_score(func, all_functions)
            importance = self._determine_importance_level(score)
            
            ranked.append(RankedDependency(
                name=func['name'],
                type=DependencyType.CALLED_FUNCTION,
                importance=importance,
                score=score,
                data=func
            ))
        
        # Sort by score descending
        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked
    
    def rank_data_structures(self, data_structures: List[Dict[str, Any]]) -> List[RankedDependency]:
        """Rank data structures by importance"""
        ranked = []
        
        for struct in data_structures:
            score = self._calculate_data_structure_score(struct)
            importance = self._determine_importance_level(score)
            
            ranked.append(RankedDependency(
                name=struct['name'],
                type=DependencyType.DATA_STRUCTURE,
                importance=importance,
                score=score,
                data=struct
            ))
        
        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked
    
    def rank_macros(self, macros: List[str], macro_definitions: List[Dict[str, Any]]) -> List[RankedDependency]:
        """Rank macros by importance"""
        ranked = []
        
        # Create a mapping of macro names to their definitions
        macro_def_map = {defn['name']: defn for defn in macro_definitions}
        
        for macro_name in macros:
            macro_def = macro_def_map.get(macro_name, {'name': macro_name, 'definition': ''})
            score = self._calculate_macro_score(macro_name, macro_def)
            importance = self._determine_importance_level(score)
            
            ranked.append(RankedDependency(
                name=macro_name,
                type=DependencyType.MACRO,
                importance=importance,
                score=score,
                data=macro_def
            ))
        
        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked
    
    def _calculate_function_score(self, function: Dict[str, Any], 
                                 all_functions: List[Dict[str, Any]]) -> float:
        """Calculate importance score for a called function"""
        score = 0.0
        
        # Check if function is in same module
        target_file = self.target_function.get('file', '')
        func_file = function.get('location', '')
        if target_file and func_file and self._is_same_module(target_file, func_file):
            score += self.WEIGHTS['same_module']
        
        # Check for critical function patterns
        func_name = function.get('name', '')
        if any(pattern.search(func_name) for pattern in self.compiled_patterns):
            score += 2.0  # Bonus for critical functions
        
        # Estimate complexity based on parameters and return type
        complexity = self._estimate_function_complexity(function)
        score += complexity * self.WEIGHTS['complexity']
        
        return max(score, 0.1)  # Minimum score
    
    def _calculate_data_structure_score(self, data_structure: Dict[str, Any]) -> float:
        """Calculate importance score for a data structure"""
        score = 0.0
        
        # Score based on definition complexity
        definition = data_structure.get('definition', '')
        if definition:
            # Simple complexity estimate: number of lines and struct/class keywords
            lines = definition.count('\n') + 1
            has_struct = 'struct' in definition.lower()
            has_class = 'class' in definition.lower()
            
            if has_struct or has_class:
                score += lines * 0.1  # More complex structures get higher score
        
        # Check if it's a critical data structure
        name = data_structure.get('name', '')
        if any(pattern.search(name) for pattern in self.compiled_patterns):
            score += 1.5
        
        return max(score, 0.1)
    
    def _calculate_macro_score(self, macro_name: str, macro_def: Dict[str, Any]) -> float:
        """Calculate importance score for a macro"""
        score = 0.0
        
        # Check for complex macros (function-like macros)
        definition = macro_def.get('definition', '')
        if '(' in definition and ')' in definition:
            score += self.WEIGHTS['macro_complexity'] * 2
        
        # Check for critical macros
        if any(pattern.search(macro_name) for pattern in self.compiled_patterns):
            score += 1.2
        
        # Simple macros get lower scores
        if len(definition.split()) <= 3:
            score *= 0.5  # Reduce score for simple macros
        
        return max(score, 0.05)  # Very minimum for macros
    
    def _is_same_module(self, file1: str, file2: str) -> bool:
        """Check if two files are in the same module"""
        # Simple heuristic: same directory
        from pathlib import Path
        try:
            return Path(file1).parent == Path(file2).parent
        except:
            return False
    
    def _estimate_function_complexity(self, function: Dict[str, Any]) -> float:
        """Estimate function complexity for scoring"""
        complexity = 0.0
        
        # Parameters contribute to complexity
        params = function.get('parameters', [])
        complexity += len(params) * 0.2
        
        # Complex return types
        return_type = function.get('return_type', '')
        if return_type and ('*' in return_type or 'struct' in return_type.lower()):
            complexity += 0.3
        
        return complexity
    
    def _determine_importance_level(self, score: float) -> ImportanceLevel:
        """Convert numeric score to importance level"""
        if score >= 3.0:
            return ImportanceLevel.CRITICAL
        elif score >= 1.5:
            return ImportanceLevel.HIGH
        elif score >= 0.5:
            return ImportanceLevel.MEDIUM
        else:
            return ImportanceLevel.LOW


def select_top_dependencies(ranked_dependencies: List[RankedDependency], 
                           max_count: int, 
                           min_importance: ImportanceLevel = ImportanceLevel.LOW) -> List[Any]:
    """Select top dependencies based on ranking and importance"""
    selected = []
    
    for dep in ranked_dependencies:
        if len(selected) >= max_count:
            break
        if dep.importance.value >= min_importance.value:
            selected.append(dep.data)
    
    return selected


def select_top_dependency_names(ranked_dependencies: List[RankedDependency], 
                               max_count: int, 
                               min_importance: ImportanceLevel = ImportanceLevel.LOW) -> List[str]:
    """Select top dependency names based on ranking and importance"""
    selected = []
    
    for dep in ranked_dependencies:
        if len(selected) >= max_count:
            break
        if dep.importance.value >= min_importance.value:
            selected.append(dep.name)
    
    return selected