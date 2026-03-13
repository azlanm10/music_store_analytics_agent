"""Semantic layer package: load schema definitions and build dataset sources for the Agent."""

from slackbot_agent.semantic_layer.semantic_layer import (
    DATASET_NAMES,
    load_sources,
)

__all__ = ["load_sources", "DATASET_NAMES"]

