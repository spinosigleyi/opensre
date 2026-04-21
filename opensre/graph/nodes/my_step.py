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

# NOTE(personal): default to strict_input=True in my fork because I kept
# wasting time debugging pipelines where a missing input was silently swallowed.
# Upstream defaults to False, but for my use-cases a missing input is always a bug.
DEFAULT_STRICT_INPUT = True


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

    Note:
        Unlike the upstream version, this fork does *not* skip execution
        on upstream errors by default — set ``ctx['force_skip']`` to
        ``True`` explicitly if you want early-exit behaviour.

        Also supports ``ctx['strict_input']`` (default: ``True`` in this
        fork, upstream default is ``False``). When set to ``True``, a
        missing ``INPUT_KEY`` is treated as a hard error rather than
        silently skipped. Useful when debugging pipelines where a missing
        input is always a bug.
    """
    logger.debug("node_my_step: starting")

    # Bail early if a previous node already reported a fatal error.
    # NOTE(personal): changed the check to also respect a 'force_skip' flag
    # so I can selectively bypass this node during local experiments without
    # having to remove the has_errors guard entirely.
    if has_errors(ctx) or ctx.get("force_skip", False):
        # NOTE(personal): improved log message to distinguish between the two
        # skip reasons — makes it much easier to spot force_skip vs real errors
        # when tailing logs locally.
        skip_reason = "force_skip flag set" if ctx.get("force_skip", False) else "upstream errors exist"
        logger.warning(
            "node_my_step: skipping execution because %s", skip_reason
        )
        return ctx

    # -----------------------------------------------
