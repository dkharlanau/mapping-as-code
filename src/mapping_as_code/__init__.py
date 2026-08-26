"""Mapping as Code public API."""

from .adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)
from .core import Diagnostic, diff_documents, lineage_graph, lineage_mermaid, validate_document
from .io import load_document
from .tabular import ImportErrorDetail, import_rows, import_tabular

__all__ = [
    "Diagnostic",
    "ImportErrorDetail",
    "diff_documents",
    "import_rows",
    "import_tabular",
    "lineage_graph",
    "lineage_mermaid",
    "load_document",
    "to_enterprise_change_graph",
    "to_reconciliation",
    "to_transformation_graph",
    "to_visual_workbench",
    "validate_document",
]

__version__ = "0.3.0"
