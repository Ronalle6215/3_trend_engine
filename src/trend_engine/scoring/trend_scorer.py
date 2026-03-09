"""
Trend scorer — computes trend scores using features + weights, enriched by Gemini
"""

import json
import re
from typing import List

from trend_engine.core.logging import get_logger
from trend_engine.core.models import TopicCluster, TrendResult
from trend_engine.config.settings import settings
from trend_engine.scoring.trend_features import compute_features
from trend_engine.scoring.weights import get_weights

logger = get_logger(__name__)


class TrendScorer:
    def score(self, clusters: List[TopicCluster], top_n: int = 20) -> List[TrendResult]:
        weights = get_weights()
        scored: list[tuple[float, TopicCluster, dict]] = []

        for cluster in clusters:
            features = compute_features(cluster)

            # Weighted score
            total = sum(features.get(k, 0) * w for k, w in weights.items())
            confidence = min(1.0, len(cluster.sources_present) / 3.0)

            scored.append((total, cluster, features))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_n]

        # Determine trend type based on features
        results = []
        for total_score, cluster, features in top:
            trend_type = self._classify_trend(features)
            results.append(TrendResult(
                trend_id=f"trend_{cluster.topic_id}",
                topic=cluster.canonical_name,
                trend_type=trend_type,
                trend_score=round(total_score, 2),
                confidence=round(min(1.0, len(cluster.sources_present) / 3.0), 2),
                time_window=settings.default_window,
                why_trending=self._generate_reasons(cluster, features),
                sources=cluster.sources_present,
                evidence=self._build_evidence(cluster),
                suggested_actions={},
            ))

        # Enrich with Gemini explanations (batch)
        if results and settings.gemini_api_key:
            results = self._enrich_with_gemini(results)

        logger.info(f"Scored {len(results)} trends (top {top_n})")
        return results

    def _classify_trend(self, features: dict[str, float]) -> str:
        if features.get("volume", 0) > 70:
            return "viral"
        elif features.get("diversity", 0) > 60:
            return "cross_platform"
        elif features.get("mentions", 0) > 50:
            return "rising"
        return "emerging"

    def _generate_reasons(self, cluster: TopicCluster, features: dict[str, float]) -> list[str]:
        reasons = []
        vol = cluster.signals_summary.get("total_volume", 0)
        mentions = cluster.signals_summary.get("total_mentions", 0)
        sources = len(cluster.sources_present)

        if vol > 100:
            reasons.append(f"High signal volume ({vol:,})")
        if sources >= 2:
            reasons.append(f"Appears across {sources} platforms ({', '.join(cluster.sources_present)})")
        if mentions >= 3:
            reasons.append(f"Mentioned {mentions} times across sources")
        if features.get("volume", 0) > 50:
            reasons.append("Strong search/engagement signals")

        return reasons or ["Detected in trend monitoring"]

    def _build_evidence(self, cluster: TopicCluster) -> list[dict]:
        items = cluster.signals_summary.get("items", [])
        evidence = []
        for item in items[:5]:
            ev = {"source": item.get("source", ""), "text": item.get("text", "")}
            if item.get("url"):
                ev["url"] = item["url"]
            if item.get("volume"):
                ev["volume"] = item["volume"]
            evidence.append(ev)
        return evidence

    def _enrich_with_gemini(self, results: List[TrendResult]) -> List[TrendResult]:
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.gemini_api_key)
            model = genai.GenerativeModel("gemini-2.0-flash")

            topics_summary = "\n".join(
                f"- {r.topic} (score: {r.trend_score}, sources: {', '.join(r.sources)})"
                for r in results[:10]
            )

            prompt = (
                f"You are a trend analyst for the Vietnamese market. "
                f"For each trend below, provide:\n"
                f"1. A brief 'why_trending' explanation (1-2 sentences, in Vietnamese)\n"
                f"2. Suggested actions for content/marketing teams (2-3 bullet points, in Vietnamese)\n\n"
                f"Trends:\n{topics_summary}\n\n"
                f"Return ONLY a JSON array where each element has: "
                f'{{"topic": "...", "why": "...", "actions": ["...", "..."]}}'
            )

            response = model.generate_content(prompt)
            text = response.text.strip()

            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                enrichments = json.loads(json_match.group(0))
                enrich_map = {e.get("topic", "").lower(): e for e in enrichments}

                for result in results:
                    match = enrich_map.get(result.topic.lower())
                    if match:
                        if match.get("why"):
                            result.why_trending.insert(0, match["why"])
                        if match.get("actions"):
                            result.suggested_actions = {"content_marketing": match["actions"]}

                logger.info(f"Gemini enriched {len(enrichments)} trends with explanations")

        except Exception as e:
            logger.warning(f"Gemini enrichment failed: {e}")

        return results
