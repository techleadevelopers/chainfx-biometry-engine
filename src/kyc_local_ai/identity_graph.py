from __future__ import annotations

from typing import Any


def build_identity_graph(payload: dict[str, Any], embedding_hash: str) -> dict[str, Any]:
    nodes = [
        {"type": "user", "id": payload.get("UserID", "")},
        {"type": "device", "id": payload.get("DeviceFingerprint", "")},
        {"type": "face", "id": embedding_hash},
        {"type": "document", "id": payload.get("DocumentHash", "")},
        {"type": "ip", "id": payload.get("IPAddress", "")},
        {"type": "phone", "id": payload.get("Phone", "")},
        {"type": "email", "id": payload.get("Email", "")},
        {"type": "wallet", "id": payload.get("WalletAddress", "")},
        {"type": "pix_key", "id": payload.get("PixKey", "")},
    ]
    present_nodes = [node for node in nodes if node["id"]]
    edges = []
    user_id = payload.get("UserID", "")
    if user_id:
        for node in present_nodes:
            if node["type"] != "user":
                edges.append({"from": user_id, "to": node["id"], "relation": f"user_has_{node['type']}"})
    return {
        "nodes": present_nodes,
        "edges": edges,
        "duplicate_detection": {
            "method": "external_vector_index_hook",
            "top_k": 20,
            "status": "not_persisted_by_provider",
        },
    }
