"""Mapping as Code public API."""

from .adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)
from .artifacts import catalog_html, catalog_markdown, release_bundle, traceability_matrix
from .core import Diagnostic, diff_documents, lineage_graph, lineage_mermaid, validate_document
from .governance import breaking_change_report, policy_diagnostics, quality_scorecard, validation_report
from .io import load_document
from .tabular import ImportErrorDetail, import_rows, import_tabular

__all__ = [
    "Diagnostic",
    "ImportErrorDetail",
    "breaking_change_report",
    "catalog_html",
    "catalog_markdown",
    "diff_documents",
    "import_rows",
    "import_tabular",
    "lineage_graph",
    "lineage_mermaid",
    "load_document",
    "policy_diagnostics",
    "quality_scorecard",
    "release_bundle",
    "to_enterprise_change_graph",
    "to_reconciliation",
    "to_transformation_graph",
    "to_visual_workbench",
    "traceability_matrix",
    "validate_document",
    "validation_report",
]

__version__ = "0.4.0"
