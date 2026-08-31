"""Mapping as Code public API."""

from .adapters import (
    to_enterprise_change_graph,
    to_reconciliation,
    to_transformation_graph,
    to_visual_workbench,
)
from .annotations import github_annotations
from .artifacts import catalog_html, catalog_markdown, release_bundle, traceability_matrix
from .catalog_index import build_catalog_index, search_catalog
from .change_projection import to_enterprise_change_transition
from .composition import CompositionError, compose_manifest
from .contracts import TARGET_CONTRACTS
from .core import Diagnostic, diff_documents, lineage_graph, lineage_mermaid, validate_document
from .ecosystem import ecosystem_bundle
from .governance import breaking_change_report, policy_diagnostics, quality_scorecard, validation_report
from .graph_exports import lineage_cypher, lineage_graphml
from .interface_binding import bind_interface_contract
from .io import load_document
from .performance import benchmark_mapping, synthetic_mapping
from .review import review_markdown, review_report
from .sarif import sarif_report
from .tabular import ImportErrorDetail, import_rows, import_tabular

__all__ = [
    "CompositionError",
    "Diagnostic",
    "ImportErrorDetail",
    "TARGET_CONTRACTS",
    "bind_interface_contract",
    "benchmark_mapping",
    "breaking_change_report",
    "catalog_html",
    "catalog_markdown",
    "build_catalog_index",
    "compose_manifest",
    "diff_documents",
    "ecosystem_bundle",
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
    "sarif_report",
    "search_catalog",
    "synthetic_mapping",
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
