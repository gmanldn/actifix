"""
Enhanced error classification taxonomy for Actifix.

This module provides sophisticated error classification based on error types,
keywords, patterns, and context to improve priority assignment and remediation.
"""

import re
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from .raise_af import TicketPriority


class ErrorCategory(Enum):
    """High-level error categories for classification."""
    SYSTEM = "system"
    DATABASE = "database"
    NETWORK = "network"
    SECURITY = "security"
    PERFORMANCE = "performance"
    VALIDATION = "validation"
    INTEGRATION = "integration"
    BUSINESS_LOGIC = "business_logic"
    CONFIGURATION = "configuration"
    RESOURCE = "resource"


class ErrorSeverity(Enum):
    """Error severity levels for impact assessment."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


@dataclass
class ErrorPattern:
    """Represents an error pattern for classification."""
    name: str
    category: ErrorCategory
    severity: ErrorSeverity
    priority: TicketPriority
    keywords: List[str]
    regex_patterns: List[str]
    description: str
    remediation_hints: List[str]


class ErrorClassifier:
    """Advanced error classifier using patterns and machine learning."""
    
    def __init__(self) -> None:
        self.patterns = self._load_error_patterns()
        self.keyword_index = self._build_keyword_index()
        
    def classify_error(
        self, 
        error_type: str, 
        message: str, 
        source: str = "",
        stack_trace: str = ""
    ) -> Tuple[ErrorCategory, ErrorSeverity, TicketPriority, List[str]]:
        """
        Classify an error and return category, severity, priority, and hints.
        
        Args:
            error_type: Type of the error (e.g., 'ValueError', 'ConnectionError')
            message: Error message text
            source: Source location where error occurred
            stack_trace: Full stack trace if available
            
        Returns:
            Tuple of (category, severity, priority, remediation_hints)
        """
        # Combine all text for analysis
        full_text = f"{error_type} {message} {source} {stack_trace}".lower()
        
        # Find matching patterns
        matches = []
        for pattern in self.patterns:
            score = self._calculate_pattern_score(pattern, full_text, error_type)
            if score > 0:
                matches.append((pattern, score))
        
        # Sort by score and get best match
        if matches:
            best_pattern = max(matches, key=lambda x: x[1])[0]
            return (
                best_pattern.category,
                best_pattern.severity,
                best_pattern.priority,
                best_pattern.remediation_hints
            )
        
        # Fallback classification
        return self._fallback_classification(error_type, message)
    
    def _calculate_pattern_score(self, pattern: ErrorPattern, text: str, error_type: str) -> float:
        """Calculate how well a pattern matches the error."""
        score = 0.0
        
        # Check error type exact match
        if error_type.lower() in [kw.lower() for kw in pattern.keywords]:
            score += 10.0
        
        # Check keyword matches
        keyword_matches = sum(1 for kw in pattern.keywords if kw.lower() in text)
        score += keyword_matches * 2.0
        
        # Check regex patterns
        regex_matches = sum(1 for regex in pattern.regex_patterns 
                          if re.search(regex, text, re.IGNORECASE))
        score += regex_matches * 5.0
        
        return score
    
    def _fallback_classification(self, error_type: str, message: str) -> Tuple[ErrorCategory, ErrorSeverity, TicketPriority, List[str]]:
        """Provide fallback classification when no patterns match."""
        # Basic classification based on error type
        error_type_lower = error_type.lower()
        
        if any(term in error_type_lower for term in ['connection', 'network', 'timeout']):
            return (ErrorCategory.NETWORK, ErrorSeverity.HIGH, TicketPriority.P1, 
                   ["Check network connectivity", "Verify service endpoints"])
        
        if any(term in error_type_lower for term in ['database', 'sql', 'db']):
            return (ErrorCategory.DATABASE, ErrorSeverity.HIGH, TicketPriority.P1,
                   ["Check database connection", "Verify database schema"])
        
        if any(term in error_type_lower for term in ['permission', 'access', 'auth']):
            return (ErrorCategory.SECURITY, ErrorSeverity.HIGH, TicketPriority.P1,
                   ["Check permissions", "Verify authentication"])
        
        if any(term in error_type_lower for term in ['value', 'type', 'attribute']):
            return (ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, TicketPriority.P2,
                   ["Validate input parameters", "Check data types"])
        
        # Default classification
        return (ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM, TicketPriority.P2,
               ["Review error context", "Check business logic"])
    
    def _build_keyword_index(self) -> Dict[str, List[ErrorPattern]]:
        """Build an index of keywords to patterns for fast lookup."""
        index = {}
        for pattern in self.patterns:
            for keyword in pattern.keywords:
                if keyword not in index:
                    index[keyword] = []
                index[keyword].append(pattern)
        return index
    
    def _load_error_patterns(self) -> List[ErrorPattern]:
        """Load predefined error patterns."""
        return [
            # System Critical Errors
            ErrorPattern(
                name="system_crash",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                priority=TicketPriority.P0,
                keywords=["fatal", "crash", "segfault", "core dump", "system failure"],
                regex_patterns=[r"fatal.*error", r"system.*crash", r"segmentation.*fault"],
                description="Critical system failure requiring immediate attention",
                remediation_hints=[
                    "Restart system immediately",
                    "Check system logs for root cause",
                    "Verify system resources",
                    "Contact system administrator"
                ]
            ),
            
            # Database Errors
            ErrorPattern(
                name="database_corruption",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.CRITICAL,
                priority=TicketPriority.P0,
                keywords=["database corrupt", "db corruption", "sqlite corrupt", "data loss"],
                regex_patterns=[r"database.*corrupt", r"sqlite.*corrupt", r"data.*corrupt"],
                description="Database corruption detected",
                remediation_hints=[
                    "Stop all database operations",
                    "Restore from backup",
                    "Run database integrity check",
                    "Contact database administrator"
                ]
            ),
            
            ErrorPattern(
                name="database_connection",
                category=ErrorCategory.DATABASE,
                severity=ErrorSeverity.HIGH,
                priority=TicketPriority.P1,
                keywords=["connection refused", "database locked", "timeout", "connection error"],
                regex_patterns=[r"connection.*refused", r"database.*locked", r"connection.*timeout"],
                description="Database connection issues",
                remediation_hints=[
                    "Check database service status",
                    "Verify connection parameters",
                    "Check network connectivity",
                    "Review connection pool settings"
                ]
            ),
            
            # Security Errors
            ErrorPattern(
                name="authentication_failure",
                category=ErrorCategory.SECURITY,
                severity=ErrorSeverity.HIGH,
                priority=TicketPriority.P1,
                keywords=["authentication failed", "invalid credentials", "access denied", "unauthorized"],
                regex_patterns=[r"auth.*fail", r"access.*denied", r"unauthorized.*access"],
                description="Authentication or authorization failure",
                remediation_hints=[
                    "Verify credentials",
                    "Check user permissions",
                    "Review authentication configuration",
                    "Check for security policy changes"
                ]
            ),
            
            # Network Errors
            ErrorPattern(
                name="network_timeout",
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.HIGH,
                priority=TicketPriority.P1,
                keywords=["connection timeout", "network timeout", "request timeout", "socket timeout"],
                regex_patterns=[r"timeout.*error", r"connection.*timeout", r"socket.*timeout"],
                description="Network timeout or connectivity issues",
                remediation_hints=[
                    "Check network connectivity",
                    "Verify service endpoints",
                    "Review timeout settings",
                    "Check firewall rules"
                ]
            ),
            
            # Performance Errors
            ErrorPattern(
                name="memory_exhaustion",
                category=ErrorCategory.PERFORMANCE,
                severity=ErrorSeverity.HIGH,
                priority=TicketPriority.P1,
                keywords=["out of memory", "memory error", "allocation failed", "memory exhausted"],
                regex_patterns=[r"out.*of.*memory", r"memory.*error", r"allocation.*failed"],
                description="Memory exhaustion or allocation failure",
                remediation_hints=[
                    "Check memory usage",
                    "Identify memory leaks",
                    "Optimize memory allocation",
                    "Increase available memory"
                ]
            ),
            
            # Validation Errors
            ErrorPattern(
                name="input_validation",
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.MEDIUM,
                priority=TicketPriority.P2,
                keywords=["invalid input", "validation error", "bad request", "malformed data"],
                regex_patterns=[r"invalid.*input", r"validation.*error", r"malformed.*data"],
                description="Input validation or data format errors",
                remediation_hints=[
                    "Validate input parameters",
                    "Check data format requirements",
                    "Review validation rules",
                    "Sanitize user input"
                ]
            ),
            
            # Configuration Errors
            ErrorPattern(
                name="configuration_error",
                category=ErrorCategory.CONFIGURATION,
                severity=ErrorSeverity.MEDIUM,
                priority=TicketPriority.P2,
                keywords=["config error", "configuration invalid", "missing config", "bad config"],
                regex_patterns=[r"config.*error", r"configuration.*invalid", r"missing.*config"],
                description="Configuration or setup errors",
                remediation_hints=[
                    "Check configuration files",
                    "Verify environment variables",
                    "Review default settings",
                    "Validate configuration syntax"
                ]
            ),
            
            # Resource Errors
            ErrorPattern(
                name="disk_space",
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.HIGH,
                priority=TicketPriority.P1,
                keywords=["disk full", "no space", "disk space", "storage full"],
                regex_patterns=[r"disk.*full", r"no.*space.*left", r"storage.*full"],
                description="Disk space or storage issues",
                remediation_hints=[
                    "Free up disk space",
                    "Clean temporary files",
                    "Archive old data",
                    "Monitor disk usage"
                ]
            ),
            
            # Integration Errors
            ErrorPattern(
                name="api_failure",
                category=ErrorCategory.INTEGRATION,
                severity=ErrorSeverity.MEDIUM,
                priority=TicketPriority.P2,
                keywords=["api error", "service unavailable", "external service", "integration failed"],
                regex_patterns=[r"api.*error", r"service.*unavailable", r"integration.*failed"],
                description="External API or service integration failures",
                remediation_hints=[
                    "Check external service status",
                    "Verify API endpoints",
                    "Review integration configuration",
                    "Implement retry logic"
                ]
            ),
            # High-Value Ideas (down-classify to P2)
            ErrorPattern(
                name="high_value_ideas",
                category=ErrorCategory.BUSINESS_LOGIC,
                severity=ErrorSeverity.MEDIUM,
                priority=TicketPriority.P2,
                keywords=["high-value", "hv", "ideas", "interop"],
                regex_patterns=[r"high[-_]?value", r"ideas/high_value", r"run label.*high-value-ideas", r"dashboard ideas"],
                description="High-value feature ideas from dashboard Ideas pane",
                remediation_hints=[
                    "Group similar ideas into consolidated tickets",
                    "Prioritize based on business impact",
                    "Implement backlog grooming for HV tickets"
                ]
            )
        ]


# Global classifier instance
_classifier = None

def get_error_classifier() -> ErrorClassifier:
    """Get the global error classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = ErrorClassifier()
    return _classifier


def classify_error(error_type: str, message: str, source: str = "", stack_trace: str = "") -> Dict:
    """
    Classify an error and return classification details.
    
    Args:
        error_type: Type of the error
        message: Error message
        source: Source location
        stack_trace: Stack trace if available
        
    Returns:
        Dictionary with classification details
    """
    classifier = get_error_classifier()
    category, severity, priority, hints = classifier.classify_error(
        error_type, message, source, stack_trace
    )
    
    return {
        "category": category.value,
        "severity": severity.value,
        "priority": priority,
        "remediation_hints": hints,
        "classification_confidence": "high" if hints else "medium"
    }


def get_error_patterns() -> List[ErrorPattern]:
    """Get all available error patterns."""
    classifier = get_error_classifier()
    return classifier.patterns


def add_custom_pattern(pattern: ErrorPattern) -> None:
    """Add a custom error pattern to the classifier."""
    classifier = get_error_classifier()
    classifier.patterns.append(pattern)
    classifier.keyword_index = classifier._build_keyword_index()
