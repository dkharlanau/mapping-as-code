"""Mapping as Code public API."""

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
    "validate_document",
]

__version__ = "0.2.0"
