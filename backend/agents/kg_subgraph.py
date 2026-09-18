"""
Knowledge Graph Subgraph Extractor
==================================
Extracts localized egocentric subgraphs for interactive visualization.
Computes top occupational transition pathways and skill-vector projections.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

def extract_subgraph(kg, node_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    if kg is None:
        return {"nodes": [], "links": [], "central_node": None}

    # If no node specified or not found, pick Software Developers (15-1252.00) or first node
    if not node_id or node_id not in kg:
        target = "15-1252.00" if "15-1252.00" in kg else list(kg.nodes())[0]
    else:
        target = node_id

    central_data = kg.nodes[target]
    central_title = central_data.get("title", str(target))
    central_desc = central_data.get("description", "")

    # Get neighbors sorted by cosine similarity
    nbr_list = []
    for nbr in kg.neighbors(target):
        edge_data = kg.get_edge_data(target, nbr) or {}
        sim = edge_data.get("cosine_similarity", 0.85)
        nbr_title = kg.nodes[nbr].get("title", str(nbr))
        nbr_list.append((nbr, nbr_title, float(sim)))

    nbr_list.sort(key=lambda x: x[2], reverse=True)
    top_nbrs = nbr_list[:limit]

    nodes = [
        {
            "id": target,
            "label": central_title,
            "type": "central",
            "soc": target,
            "degree": kg.degree(target),
            "description": central_desc[:140] + ("..." if len(central_desc) > 140 else "")
        }
    ]

    links = []
    for nbr_id, nbr_title, sim in top_nbrs:
        nodes.append({
            "id": nbr_id,
            "label": nbr_title,
            "type": "neighbor",
            "soc": nbr_id,
            "degree": kg.degree(nbr_id),
            "similarity": round(sim, 4)
        })
        links.append({
            "source": target,
            "target": nbr_id,
            "weight": round(sim, 4),
            "label": f"{round(sim * 100, 1)}% transition similarity"
        })

    return {
        "central_node": {
            "id": target,
            "title": central_title,
            "soc": target,
            "degree": kg.degree(target),
            "description": central_desc
        },
        "nodes": nodes,
        "links": links,
        "available_presets": [
            {"soc": "15-1252.00", "title": "Software Developers"},
            {"soc": "15-1211.00", "title": "Computer Systems Analysts"},
            {"soc": "11-9041.00", "title": "Architectural & Engineering Managers"},
            {"soc": "11-1021.00", "title": "General and Operations Managers"},
            {"soc": "19-1042.00", "title": "Medical Scientists"}
        ]
    }