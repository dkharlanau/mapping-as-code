"""Mapping as Code public API."""

from .adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)
from .annotations import github_annotations
from .artifacts import catalog_html, catalog_markdown, release_bundle, traceability_matrix
from .change_projection import to_enterprise_change_transition
from .core import Diagnostic, diff_documents, lineage_graph, lineage_mermaid, validate_document
from .governance import breaking_change_report, policy_diagnostics, quality_scorecard, validation_report
from .graph_exports import lineage_cypher, lineage_graphml
from .interface_binding import bind_interface_contract
from .io import load_document
from .review import review_markdown, review_report
from .tabular import ImportErrorDetail, import_rows, import_tabular

__all__ = [
    "Diagnostic",
    "ImportErrorDetail",
    "bind_interface_contract",
    "breaking_change_report",
    "catalog_html",
    "catalog_markdown",
    "diff_documents",
    "github_annotations",
    "import_rows",
    "import_tabular",
    "lineage_cypher",
    "lineage_graph",
    "lineage_graphml",
    "lineage_mermaid",
    "load_document",
    "policy_diagnostics",
    "quality_scorecard",
    "release_bundle",
    "review_markdown",
    "review_report",
    "to_enterprise_change_graph",
    "to_enterprise_change_transition",
    "to_reconciliation",
    "to_transformation_graph",
    "to_visual_workbench",
    "traceability_matrix",
    "validate_document",
    "validation_report",
]

__version__ = "0.5.0"
