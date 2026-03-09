"""
Topic clustering — groups similar signal items into TopicClusters
"""

from typing import Any

from trend_engine.core.logging import get_logger
from trend_engine.core.models import TopicCluster
from trend_engine.utils.text import is_similar

logger = get_logger(__name__)


def cluster_items(
    items: list[dict[str, Any]],
    similarity_threshold: float = 0.6,
) -> list[TopicCluster]:
    """
    Cluster normalized signal items by text similarity.
    Items with similar text are grouped into the same TopicCluster.
    """
    if not items:
        return []

    clusters: list[dict[str, Any]] = []

    for item in items:
        text = item.get("text", "")
        if not text:
            continue

        matched = False
        for cluster in clusters:
            # Check similarity against cluster's canonical name and keywords
            if is_similar(text, cluster["canonical"], similarity_threshold):
                cluster["items"].append(item)
                cluster["keywords"].add(text)
                cluster["sources"].add(item.get("source", ""))
                matched = True
                break

            # Also check against all keywords in the cluster
            for kw in list(cluster["keywords"]):
                if is_similar(text, kw, similarity_threshold):
                    cluster["items"].append(item)
                    cluster["keywords"].add(text)
                    cluster["sources"].add(item.get("source", ""))
                    matched = True
                    break
            if matched:
                break

        if not matched:
            clusters.append({
                "canonical": text,
                "keywords": {text},
                "sources": {item.get("source", "")},
                "items": [item],
            })

    # Convert to TopicCluster models
    topic_clusters = []
    for i, c in enumerate(clusters):
        total_volume = sum(it.get("volume", 0) for it in c["items"])
        topic_clusters.append(TopicCluster(
            topic_id=f"cluster_{i:03d}",
            canonical_name=c["canonical"],
            keywords=sorted(c["keywords"]),
            sources_present=sorted(c["sources"]),
            signals_summary={
                "total_mentions": len(c["items"]),
                "total_volume": total_volume,
                "sources_count": len(c["sources"]),
                "items": c["items"],
            },
        ))

    logger.info(f"Clustering: {len(items)} items → {len(topic_clusters)} clusters")
    return topic_clusters
