# Logging configuration

import logging
import logging.config
import sys
import json
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from pathlib import Path
import os

from .constants import (
    LogLevel,
    DEFAULT_ENVIRONMENT,
    APP_NAME,
    APP_VERSION,
    ErrorCode,
    TransactionType,
    NotificationType
)


class FinancialEventFormatter(logging.Formatter):
    """Custom formatter for financial events with structured data"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with financial context"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "app_name": APP_NAME,
            "app_version": APP_VERSION,
            "environment": os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT)
        }

        # Add financial context if available
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'transaction_id'):
            log_entry["transaction_id"] = record.transaction_id
        if hasattr(record, 'amount'):
            log_entry["amount"] = record.amount
        if hasattr(record, 'currency'):
            log_entry["currency"] = record.currency
        if hasattr(record, 'category'):
            log_entry["category"] = record.category
        if hasattr(record, 'error_code'):
            log_entry["error_code"] = record.error_code
        if hasattr(record, 'grpc_method'):
            log_entry["grpc_method"] = record.grpc_method
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms

        # Add exception details if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class SecurityAuditFormatter(logging.Formatter):
    """Specialized formatter for security events"""

    def format(self, record: logging.LogRecord) -> str:
        """Format security audit log"""
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "security_audit",
            "level": record.levelname,
            "message": record.getMessage(),
            "app_name": APP_NAME,
            "environment": os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT)
        }

        # Security-specific fields
        if hasattr(record, 'user_id'):
            audit_entry["user_id"] = record.user_id
        if hasattr(record, 'ip_address'):
            audit_entry["ip_address"] = record.ip_address
        if hasattr(record, 'user_agent'):
            audit_entry["user_agent"] = record.user_agent
        if hasattr(record, 'action'):
            audit_entry["action"] = record.action
        if hasattr(record, 'resource'):
            audit_entry["resource"] = record.resource
        if hasattr(record, 'success'):
            audit_entry["success"] = record.success
        if hasattr(record, 'failure_reason'):
            audit_entry["failure_reason"] = record.failure_reason

        return json.dumps(audit_entry, ensure_ascii=False, default=str)


class PerformanceFormatter(logging.Formatter):
    """Formatter for performance metrics"""

    def format(self, record: logging.LogRecord) -> str:
        """Format performance log"""
        perf_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "performance",
            "level": record.levelname,
            "message": record.getMessage(),
            "app_name": APP_NAME
        }

        # Performance metrics
        if hasattr(record, 'duration_ms'):
            perf_entry["duration_ms"] = record.duration_ms
        if hasattr(record, 'grpc_method'):
            perf_entry["grpc_method"] = record.grpc_method
        if hasattr(record, 'memory_usage_mb'):
            perf_entry["memory_usage_mb"] = record.memory_usage_mb
        if hasattr(record, 'cpu_usage_percent'):
            perf_entry["cpu_usage_percent"] = record.cpu_usage_percent
        if hasattr(record, 'database_queries'):
            perf_entry["database_queries"] = record.database_queries

        return json.dumps(perf_entry, ensure_ascii=False, default=str)


def get_logging_config(
    log_level: str = "INFO",
    log_format: str = "json",
    log_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate logging configuration based on environment

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type (json, text)
        log_dir: Directory for log files (None for console only)

    Returns:
        Logging configuration dictionary
    """

    environment = os.getenv("ENVIRONMENT", DEFAULT_ENVIRONMENT)

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": FinancialEventFormatter,
            },
            "text": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "security": {
                "()": SecurityAuditFormatter,
            },
            "performance": {
                "()": PerformanceFormatter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": log_format if log_format in ["json", "text"] else "json",
                "stream": sys.stdout
            }
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            # Application loggers
            "spendywise": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "spendywise.grpc": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "spendywise.auth": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "spendywise.transactions": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "spendywise.ai": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "spendywise.financial": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            # Security audit logger
            "spendywise.security": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            # Performance logger
            "spendywise.performance": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            # Third-party loggers
            "grpc": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "sqlalchemy": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "supabase": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

    # Add file handlers for production
    if environment == "production" and log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Application log file
        config["handlers"]["app_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json",
            "filename": str(log_path / "spendywise.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }

        # Security audit log file
        config["handlers"]["security_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "security",
            "filename": str(log_path / "security_audit.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 10,
            "encoding": "utf-8"
        }

        # Performance log file
        config["handlers"]["performance_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "performance",
            "filename": str(log_path / "performance.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8"
        }

        # Error log file
        config["handlers"]["error_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": str(log_path / "errors.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 10,
            "encoding": "utf-8"
        }

        # Add file handlers to loggers
        for logger_name in ["spendywise", "spendywise.grpc", "spendywise.auth",
                           "spendywise.transactions", "spendywise.ai", "spendywise.financial"]:
            config["loggers"][logger_name]["handlers"].extend(["app_file", "error_file"])

        config["loggers"]["spendywise.security"]["handlers"].append("security_file")
        config["loggers"]["spendywise.performance"]["handlers"].append("performance_file")

    return config


def setup_logging(
    log_level: Optional[str] = None,
    log_format: str = "json",
    log_dir: Optional[str] = None
) -> None:
    """
    Setup logging configuration

    Args:
        log_level: Logging level override
        log_format: Format type (json, text)
        log_dir: Directory for log files
    """
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    config = get_logging_config(log_level, log_format, log_dir)
    logging.config.dictConfig(config)


class FinancialLogger:
    """Enhanced logger for financial operations"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(f"spendywise.{name}")

    def log_transaction(
        self,
        user_id: str,
        transaction_type: TransactionType,
        amount: float,
        currency: str,
        category: str,
        transaction_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log financial transaction"""
        self.logger.info(
            f"Transaction {transaction_type.value}: {amount} {currency}",
            extra={
                "user_id": user_id,
                "transaction_id": transaction_id,
                "transaction_type": transaction_type.value,
                "amount": amount,
                "currency": currency,
                "category": category,
                "extra_data": extra_data or {}
            }
        )

    def log_budget_event(
        self,
        user_id: str,
        event_type: str,
        budget_id: str,
        amount: float,
        currency: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log budget-related events"""
        self.logger.info(
            f"Budget {event_type}: {amount} {currency}",
            extra={
                "user_id": user_id,
                "budget_id": budget_id,
                "event_type": event_type,
                "amount": amount,
                "currency": currency,
                "extra_data": extra_data or {}
            }
        )

    def log_ai_interaction(
        self,
        user_id: str,
        query: str,
        response_type: str,
        duration_ms: float,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log AI advisor interactions"""
        self.logger.info(
            f"AI interaction: {response_type}",
            extra={
                "user_id": user_id,
                "query": query[:100],  # Truncate for privacy
                "response_type": response_type,
                "duration_ms": duration_ms,
                "extra_data": extra_data or {}
            }
        )

    def log_error(
        self,
        error_code: ErrorCode,
        message: str,
        user_id: Optional[str] = None,
        exception: Optional[Exception] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log application errors"""
        self.logger.error(
            message,
            extra={
                "error_code": error_code.value,
                "user_id": user_id,
                "extra_data": extra_data or {}
            },
            exc_info=exception
        )


class SecurityLogger:
    """Specialized logger for security events"""

    def __init__(self):
        self.logger = logging.getLogger("spendywise.security")

    def log_auth_attempt(
        self,
        user_id: Optional[str],
        action: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        failure_reason: Optional[str] = None
    ) -> None:
        """Log authentication attempts"""
        self.logger.info(
            f"Auth {action}: {'Success' if success else 'Failed'}",
            extra={
                "user_id": user_id,
                "action": action,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "failure_reason": failure_reason
            }
        )

    def log_permission_check(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        ip_address: str
    ) -> None:
        """Log permission checks"""
        self.logger.info(
            f"Permission {action} on {resource}: {'Granted' if granted else 'Denied'}",
            extra={
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "success": granted,
                "ip_address": ip_address
            }
        )


class PerformanceLogger:
    """Logger for performance metrics"""

    def __init__(self):
        self.logger = logging.getLogger("spendywise.performance")

    def log_grpc_call(
        self,
        method: str,
        duration_ms: float,
        success: bool,
        user_id: Optional[str] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None
    ) -> None:
        """Log gRPC call performance"""
        self.logger.info(
            f"gRPC {method}: {duration_ms}ms",
            extra={
                "grpc_method": method,
                "duration_ms": duration_ms,
                "success": success,
                "user_id": user_id,
                "request_size": request_size,
                "response_size": response_size
            }
        )

    def log_database_query(
        self,
        query_type: str,
        duration_ms: float,
        table: str,
        rows_affected: Optional[int] = None
    ) -> None:
        """Log database query performance"""
        self.logger.info(
            f"DB {query_type} on {table}: {duration_ms}ms",
            extra={
                "query_type": query_type,
                "duration_ms": duration_ms,
                "table": table,
                "rows_affected": rows_affected
            }
        )


# Convenience functions for getting specialized loggers
def get_financial_logger(name: str) -> FinancialLogger:
    """Get a financial logger instance"""
    return FinancialLogger(name)


def get_security_logger() -> SecurityLogger:
    """Get the security logger instance"""
    return SecurityLogger()


def get_performance_logger() -> PerformanceLogger:
    """Get the performance logger instance"""
    return PerformanceLogger()


# Initialize logging on module import
setup_logging()
