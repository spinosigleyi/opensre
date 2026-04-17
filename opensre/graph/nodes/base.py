"""Base node definition for the OpenSRE graph execution engine.

All graph nodes must inherit from BaseNode and implement the required
interface defined here. This ensures consistent behavior across the
execution pipeline.
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class NodeContext:
    """Execution context passed between nodes in the graph."""

    run_id: str
    params: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set_result(self, key: str, value: Any) -> None:
        """Store a result value under the given key."""
        self.results[key] = value

    def get_result(self, key: str, default: Any = None) -> Any:
        """Retrieve a previously stored result."""
        return self.results.get(key, default)

    def add_error(self, message: str) -> None:
        """Append an error message to the context error list."""
        logger.error("[run_id=%s] Node error: %s", self.run_id, message)
        self.errors.append(message)

    @property
    def has_errors(self) -> bool:
        """Return True if any errors have been recorded."""
        return len(self.errors) > 0

    def clear_errors(self) -> None:
        """Clear all recorded errors. Useful when retrying a node after handling errors."""
        self.errors.clear()

    def merge_params(self, overrides: Dict[str, Any]) -> None:
        """Merge additional parameters into ctx.params, overwriting existing keys.

        Handy for injecting runtime config without replacing the entire params dict.
        """
        self.params.update(overrides)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the context to a plain dict, useful for logging or debugging."""
        return {
            "run_id": self.run_id,
            "params": self.params,
            "results": self.results,
            "errors": self.errors,
            "metadata": self.metadata,
        }

    def snapshot(self) -> Dict[str, Any]:
        """Return a shallow copy of the context as a dict.

        Useful for capturing state at a point in time without mutating the original.
        Personal note: handy when debugging multi-step pipelines locally.
        """
        d = self.to_dict()
        d["params"] = dict(self.params)
        d["results"] = dict(self.results)
        d["errors"] = list(self.errors)
        d["metadata"] = dict(self.metadata)
        return d


class BaseNode(abc.ABC):
    """Abstract base class for all OpenSRE graph nodes.

    Subclasses must implement `node_id`, `is_available`, and `run`.
    Optionally override `extract_params` to parse node-specific
    parameters from the incoming context.
    """

    #: Unique identifier for this node type (snake_case).
    node_id: str = ""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Skip enforcement for intermediate abstract classes that don't yet
        # define node_id (e.g. mixins or partial base classes).
        if not abc.ABC in cls.__bases__ and not getattr(cls, "node_id", ""):
            raise TypeError(
                f"Node subclass '{cls.__name__}' must define a non-empty 'node_id'."
            )

   