"""Mapping as Code public API."""

from .core import Diagnostic, diff_documents, lineage_graph, lineage_mermaid, validate_document
from .io import load_document

__all__ = [
    "Diagnostic",
    "diff_documents",
    "lineage_graph",
    "lineage_mermaid",
    "load_document",
    "validate_document",
]

__version__ = "0.1.0"
