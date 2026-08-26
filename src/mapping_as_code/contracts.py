from __future__ import annotations

from typing import Any

TARGET_CONTRACTS: dict[str, dict[str, Any]] = {
    "transformation-graph": {
        "version": "0.1",
        "source_blob_sha": "307eef2d68a7aa4880dc0b16d0ddc14c27d3ada8",
        "source": "dkharlanau/transformation-graph:schema/transformation-graph.schema.json",
    },
    "reconciliation-as-code": {
        "version": 1,
        "source_blob_sha": "b181b096a05fc1785165864d94d555804c1f45d0",
        "source": "dkharlanau/reconciliation-as-code:schema/reconciliation.schema.json",
    },
    "enterprise-change-graph": {
        "version": 1,
        "source_blob_sha": "4b87b70f6d158c54e0daa4bc3eeda4f618eb9e94",
        "source": "dkharlanau/enterprise-change-graph:schema/enterprise-change-graph.schema.json",
    },
    "visual-workbench": {
        "version": 1,
        "source_blob_sha": "b9b6211977d73b69786b4199a5e06a88d7f3634b",
        "source": "dkharlanau/visual-workbench:schemas/visual-workbench.schema.json",
    },
    "interface-as-code": {
        "version": "1.0",
        "source_blob_sha": "87455d9d0921007b5efed1d6dd252b65a075a761",
        "source": "dkharlanau/interface-as-code:spec/v1.0/interface.schema.json",
    },
}
