"""my_step node implementation for the opensre graph pipeline.

This module implements the `node_my_step` node as defined in the
graph-nodes cursor rules. It processes a single unit of work within
the directed graph, reads inputs from NodeContext, performs its logic,
and writes results back to the context.
"""

from __future__ import annotations

import logging
from typing import Any

from opensre.graph.nodes.base import (
    NodeContext,
    add_error,
    get_result,
    has_errors,
    set_result,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Key used to store this node's output in the shared NodeContext.
STEP_RESULT_KEY = "my_step_result"

#: Key this node reads from upstream nodes.
INPUT_KEY = "my_step_input"


# ---------------------------------------------------------------------------
# Node implementation
# ---------------------------------------------------------------------------


def node_my_step(ctx: NodeContext) -> NodeContext:
    """Execute the *my_step* graph node.

    Reads ``INPUT_KEY`` from *ctx*, applies the step's transformation
    logic, and writes the result under ``STEP_RESULT_KEY``.  Any
    recoverable error is recorded via :func:`add_error` so that
    downstream nodes can inspect :func:`has_errors` before proceeding.

    Args:
        ctx: Shared mutable context object passed along the graph edges.

    Returns:
        The same *ctx* instance with ``STEP_RESULT_KEY`` populated on
        success, or with an error entry on failure.
    """
    logger.debug("node_my_step: starting")

    # Bail early if a previous node already reported a fatal error.
    if has_errors(ctx):
        logger.warning(
            "node_my_step: skipping execution because upstream errors exist"
        )
        return ctx

    # ------------------------------------------------------------------ #
    # 1. Read input
    # ------------------------------------------------------------------ #
    raw_input: Any = get_result(ctx, INPUT_KEY)
    if raw_input is None:
        add_error(
            ctx,
            node="my_step",
            message=f"Required input '{INPUT_KEY}' is missing from context.",
        )
        logger.error("node_my_step: missing input key '%s'", INPUT_KEY)
        return ctx

    # ------------------------------------------------------------------ #
    # 2. Core transformation logic
    # ------------------------------------------------------------------ #
    try:
        processed = _transform(raw_input)
    except Exception as exc:  # noqa: BLE001
        add_error(
            ctx,
            node="my_step",
            message=f"Transformation failed: {exc}",
        )
        logger.exception("node_my_step: unhandled exception during transform")
        return ctx

    # ------------------------------------------------------------------ #
    # 3. Write output
    # ------------------------------------------------------------------ #
    set_result(ctx, STEP_RESULT_KEY, processed)
    logger.debug("node_my_step: completed successfully, result stored under '%s'", STEP_RESULT_KEY)

    return ctx


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _transform(data: Any) -> dict[str, Any]:
    """Apply the step's business logic to *data*.

    Currently normalises the input into a canonical dict representation.
    Replace or extend this function with domain-specific processing.

    Args:
        data: Raw input value retrieved from the upstream node.

    Returns:
        A dictionary containing the processed output.

    Raises:
        TypeError: If *data* cannot be coerced into a supported type.
    """
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if v is not None}

    if isinstance(data, (list, tuple)):
        return {"items": list(data), "count": len(data)}

    if isinstance(data, str):
        return {"value": data.strip(), "length": len(data.strip())}

    raise TypeError(
        f"_transform received unsupported type {type(data).__name__!r}; "
        "expected dict, list, tuple, or str."
    )
