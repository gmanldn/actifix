"""Plugin sandboxing: isolation, capability control, and timeout enforcement.

Consolidates 25 plugin sandbox tickets with:
- Thread pool isolation with timeout enforcement
- Explicit plugin API contract and version negotiation
- Capability flags (database, network, filesystem) with deny-by-default
- Early metadata validation with fast failure
- Timeout enforcement and structured failure tickets
- Misbehavior isolation prevents core crashes
"""

from __future__ import annotations

import logging
import time
import threading
from contextlib import suppress
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Set, List, Tuple, Callable, Dict
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from .protocol import Plugin
from .registry import PluginRegistry
from .validation import validate_plugin
from ..raise_af import record_error, TicketPriority
from ..log_utils import log_event
from ..agent_voice import record_agent_voice

logger = logging.getLogger(__name__)


class PluginCapability(Enum):
    """Plugin capability flags (deny-by-default)."""
    DATABASE = "database"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    SUBPROCESS = "subprocess"


@dataclass
class PluginMetadata:
    """Plugin metadata for validation and capability tracking."""
    name: str
    version: str
    author: str
    description: str = ""
    capabilities: Set[PluginCapability] = field(default_factory=set)
    min_api_version: str = "1.0.0"
    max_api_version: str = "999.0.0"

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate plugin metadata.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        if not self.name:
            errors.append("Plugin name is required")
        if not self.version:
            errors.append("Plugin version is required")
        if not self.author:
            errors.append("Plugin author is required")

        return len(errors) == 0, errors


@dataclass
class PluginExecutionContext:
    """Context for plugin execution with timeout and capability enforcement."""
    plugin_name: str
    plugin_version: str
    capabilities: Set[PluginCapability]
    timeout_seconds: float = 30.0
    start_time: float = field(default_factory=time.time)
    ended_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    timed_out: bool = False

    def elapsed_seconds(self) -> float:
        """Get elapsed time since execution started."""
        end = self.ended_at or time.time()
        return end - self.start_time

    def has_capability(self, capability: PluginCapability) -> bool:
        """Check if plugin has a capability."""
        return capability in self.capabilities


@dataclass
class PluginFailure:
    """Represents a plugin execution failure."""
    plugin_name: str
    error: str
    timed_out: bool = False

    def __repr__(self) -> str:
        status = "TIMEOUT" if self.timed_out else "FAILED"
        return f"<PluginFailure {self.plugin_name}: {status}>"


class PluginSandbox:
    """Gracefully handle plugin errors with isolation, capability control, and timeout enforcement."""

    # Plugin API version
    API_VERSION = "1.0.0"

    def __init__(
        self,
        name: str,
        max_workers: int = 4,
        default_timeout_s: float = 30.0,
    ) -> None:
        """Initialize plugin sandbox.

        Args:
            name: Sandbox name
            max_workers: Max concurrent plugin threads
            default_timeout_s: Default execution timeout
        """
        self.name = name
        self.max_workers = max_workers
        self.default_timeout_s = default_timeout_s
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix=f"plugin_{name}_"
        )
        self.lock = threading.Lock()
        self.execution_contexts: Dict[str, PluginExecutionContext] = {}

    def safe_register(
        self,
        plugin: Plugin,
        app: Any,
        registry: PluginRegistry,
        metadata: Optional[PluginMetadata] = None,
    ) -> None:
        """Register plugin with safety checks and metadata validation.

        Args:
            plugin: Plugin to register
            app: Application instance
            registry: Plugin registry
            metadata: Optional metadata for validation

        Raises:
            Exception: On validation or registration failure
        """
        try:
            # Early metadata validation (fail fast)
            if metadata:
                is_valid, errors = self.validate_metadata(metadata)
                if not is_valid:
                    self.record_error(
                        f"Plugin '{self.name}' metadata validation failed: {'; '.join(errors)}",
                        ValueError("Invalid plugin metadata")
                    )
                    raise ValueError(f"Metadata validation failed: {errors}")

            # Validate plugin structure
            validate_plugin(plugin)

            # Register in registry
            registry.register(plugin, app, name=self.name)
            logger.info("Plugin '%s' registered", self.name)

            record_agent_voice(
                module_key="plugin_sandbox",
                action="plugin_registered",
                details=f"Plugin registered: {self.name}"
            )

        except Exception as exc:
            self.record_error(f"Failed to register plugin '{self.name}'", exc)
            raise

    def execute_plugin(
        self,
        plugin_name: str,
        handler: Callable[..., Any],
        capabilities: Optional[Set[PluginCapability]] = None,
        timeout_seconds: Optional[float] = None,
        **kwargs
    ) -> Any:
        """Execute a plugin with isolation and timeout.

        Args:
            plugin_name: Name of the plugin
            handler: Callable to execute
            capabilities: Set of required capabilities (deny-by-default)
            timeout_seconds: Execution timeout
            **kwargs: Arguments to pass to handler

        Returns:
            Plugin result or PluginFailure
        """
        capabilities = capabilities or set()
        timeout_seconds = timeout_seconds or self.default_timeout_s

        # Create execution context
        context = PluginExecutionContext(
            plugin_name=plugin_name,
            plugin_version=kwargs.get("version", "unknown"),
            capabilities=capabilities,
            timeout_seconds=timeout_seconds,
        )

        context_id = f"{plugin_name}_{int(time.time() * 1000)}"

        with self.lock:
            self.execution_contexts[context_id] = context

        try:
            # Execute in thread pool with timeout
            def wrapped_handler():
                try:
                    # Create capability-restricted context for handler
                    restricted_kwargs = self._filter_kwargs(kwargs, capabilities)
                    result = handler(**restricted_kwargs)
                    return result
                except Exception as e:
                    raise RuntimeError(f"Plugin {plugin_name} failed: {e}") from e

            future = self.executor.submit(wrapped_handler)

            try:
                context.result = future.result(timeout=timeout_seconds)
                context.ended_at = time.time()

                self._emit_plugin_event("plugin_execution_complete", context)

                return context.result

            except FuturesTimeoutError:
                context.timed_out = True
                context.ended_at = time.time()
                context.error = f"Plugin {plugin_name} exceeded timeout ({timeout_seconds}s)"

                self._emit_plugin_event("plugin_timeout", context)

                # Record timeout as P1 ticket
                self.record_error(
                    context.error,
                    TimeoutError(context.error),
                    priority=TicketPriority.P1,
                )

                return PluginFailure(
                    plugin_name=plugin_name,
                    error=context.error,
                    timed_out=True,
                )

        except Exception as e:
            context.error = str(e)
            context.ended_at = time.time()

            self._emit_plugin_event("plugin_execution_failed", context)

            self.record_error(
                f"Plugin {plugin_name} crashed: {e}",
                e,
                priority=TicketPriority.P2,
            )

            return PluginFailure(
                plugin_name=plugin_name,
                error=str(e),
                timed_out=False,
            )

        finally:
            with self.lock:
                if context_id in self.execution_contexts:
                    del self.execution_contexts[context_id]

    def validate_metadata(
        self,
        metadata: PluginMetadata,
    ) -> Tuple[bool, List[str]]:
        """Validate plugin metadata early (fail fast).

        Args:
            metadata: Plugin metadata to validate

        Returns:
            (is_valid, error_messages)
        """
        is_valid, basic_errors = metadata.validate()
        if not is_valid:
            return False, basic_errors

        errors = []

        # Version negotiation
        if not self._versions_compatible(metadata.min_api_version, self.API_VERSION):
            errors.append(f"Plugin requires API version {metadata.min_api_version}, "
                        f"but sandbox provides {self.API_VERSION}")

        if not self._versions_compatible(self.API_VERSION, metadata.max_api_version):
            errors.append(f"Plugin not compatible with API version {self.API_VERSION} "
                        f"(max: {metadata.max_api_version})")

        return len(errors) == 0, errors

    def check_capability(
        self,
        context: PluginExecutionContext,
        capability: PluginCapability,
    ) -> bool:
        """Check if plugin has a capability (deny-by-default).

        Args:
            context: Execution context
            capability: Capability to check

        Returns:
            True if capability is allowed
        """
        if context.has_capability(capability):
            return True

        # Log denied access
        self._emit_plugin_event("capability_denied", {
            "plugin_name": context.plugin_name,
            "capability": capability.value,
        })

        return False

    def get_active_plugins(self) -> Dict[str, PluginExecutionContext]:
        """Get all currently executing plugins.

        Returns:
            Dict of context_id -> execution context
        """
        with self.lock:
            return dict(self.execution_contexts)

    def record_error(
        self,
        message: str,
        exc: BaseException,
        priority: TicketPriority = TicketPriority.P1,
    ) -> None:
        """Record a plugin error.

        Args:
            message: Error message
            exc: Exception that occurred
            priority: Ticket priority
        """
        logger.error("%s: %s", message, exc)
        record_error(
            message=message,
            source="PluginSandbox",
            error_type="PluginExecutionError",
            run_label="plugin-architecture",
            priority=priority,
            skip_duplicate_check=True,
            skip_ai_notes=True,
            capture_context=False
        )

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the sandbox executor.

        Args:
            wait: Wait for executing plugins to complete
        """
        self.executor.shutdown(wait=wait)

    @staticmethod
    def _versions_compatible(required: str, provided: str) -> bool:
        """Check if two semantic versions are compatible.

        Args:
            required: Required version (e.g., "1.0.0")
            provided: Provided version (e.g., "1.2.0")

        Returns:
            True if compatible (major.minor must match)
        """
        try:
            req_parts = required.split('.')[:2]  # major.minor
            prov_parts = provided.split('.')[:2]  # major.minor
            return req_parts == prov_parts
        except:
            return False

    @staticmethod
    def _filter_kwargs(
        kwargs: Dict[str, Any],
        capabilities: Set[PluginCapability],
    ) -> Dict[str, Any]:
        """Filter kwargs based on capabilities (deny-by-default).

        Args:
            kwargs: Original keyword arguments
            capabilities: Allowed capabilities

        Returns:
            Filtered kwargs
        """
        filtered = {}

        # Always allow basic kwargs
        safe_keys = {"name", "version", "description"}

        for key, value in kwargs.items():
            if key in safe_keys:
                filtered[key] = value
            elif key.startswith("db_") and PluginCapability.DATABASE in capabilities:
                filtered[key] = value
            elif key.startswith("net_") and PluginCapability.NETWORK in capabilities:
                filtered[key] = value
            elif key.startswith("fs_") and PluginCapability.FILESYSTEM in capabilities:
                filtered[key] = value
            elif key.startswith("subprocess_") and PluginCapability.SUBPROCESS in capabilities:
                filtered[key] = value

        return filtered

    @staticmethod
    def _emit_plugin_event(event_type: str, details: Any) -> None:
        """Emit a plugin execution event.

        Args:
            event_type: Type of event
            details: Event details
        """
        if isinstance(details, PluginExecutionContext):
            event_dict = {
                "plugin_name": details.plugin_name,
                "plugin_version": details.plugin_version,
                "elapsed_seconds": details.elapsed_seconds(),
                "timed_out": details.timed_out,
                "error": details.error,
            }
        else:
            event_dict = details

        log_event(f"plugin:{event_type}", details=event_dict)
        record_agent_voice(
            module_key="plugin_sandbox",
            action=event_type,
            details=f"Plugin event: {event_type}"
        )
