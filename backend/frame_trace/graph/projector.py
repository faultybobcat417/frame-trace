from __future__ import annotations

from frame_trace.domain.models import GraphEdge, GraphNode, GraphPayload
from frame_trace.persistence import Database


class GraphProjector:
    def __init__(self, db: Database):
        self.db = db

    def persona_graph(self, persona_id: str) -> GraphPayload:
        persona = self.db.one("SELECT * FROM personas WHERE id=?", (persona_id,))
        if not persona:
            raise KeyError(persona_id)
        nodes = [GraphNode(id=persona_id, type="persona", label=persona.get("label") or persona_id, data={"persona_id": persona_id})]
        edges: list[GraphEdge] = []
        seen_nodes = {persona_id}
        rows = self.db.query(
            """
            SELECT a.id asset_id, a.filename, s.id source_id, s.name source_name
            FROM appearances ap
            JOIN assets a ON a.id=ap.asset_id
            JOIN sources s ON s.id=a.source_id
            WHERE ap.persona_id=?
            ORDER BY a.captured_at DESC
            LIMIT 18
            """,
            (persona_id,),
        )
        for row in rows:
            source_node = f"source:{row['source_id']}"
            asset_node = f"asset:{row['asset_id']}"
            if source_node not in seen_nodes:
                nodes.append(GraphNode(id=source_node, type="source", label=row["source_name"], data={"source_id": row["source_id"]}))
                seen_nodes.add(source_node)
            if asset_node not in seen_nodes:
                nodes.append(GraphNode(id=asset_node, type="asset", label=row["filename"], data={"asset_id": row["asset_id"]}))
                seen_nodes.add(asset_node)
            edges.append(GraphEdge(id=f"e:{persona_id}:{asset_node}", source=persona_id, target=asset_node, type="appears_in"))
            edges.append(GraphEdge(id=f"e:{asset_node}:{source_node}", source=asset_node, target=source_node, type="published_by"))
        co = self.db.query(
            """
            SELECT p2.id, p2.label, COUNT(DISTINCT ap2.asset_id) shared
            FROM appearances ap1
            JOIN appearances ap2 ON ap1.asset_id=ap2.asset_id AND ap1.persona_id <> ap2.persona_id
            JOIN personas p2 ON p2.id=ap2.persona_id
            WHERE ap1.persona_id=?
            GROUP BY p2.id,p2.label
            ORDER BY shared DESC
            LIMIT 8
            """,
            (persona_id,),
        )
        for row in co:
            if row["id"] not in seen_nodes:
                nodes.append(GraphNode(id=row["id"], type="persona", label=row.get("label") or row["id"], data={"persona_id": row["id"]}))
                seen_nodes.add(row["id"])
            edges.append(GraphEdge(id=f"co:{persona_id}:{row['id']}", source=persona_id, target=row["id"], type="co_occurs_with", data={"shared_assets": row["shared"]}))
        return GraphPayload(nodes=nodes, edges=edges)
