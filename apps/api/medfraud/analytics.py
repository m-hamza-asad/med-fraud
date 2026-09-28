from __future__ import annotations

import math
from collections import defaultdict
from decimal import Decimal
from statistics import median
from typing import Iterable


def percentile(values: Iterable[Decimal], probability: float) -> Decimal | None:
    ordered = sorted(Decimal(value) for value in values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * min(1.0, max(0.0, probability))
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = Decimal(str(position - lower))
    return ordered[lower] * (Decimal("1") - weight) + ordered[upper] * weight


def robust_summary(values: Iterable[Decimal]) -> dict[str, Decimal | int | None]:
    ordered = sorted(Decimal(value) for value in values)
    if not ordered:
        return {"count": 0, "median": None, "mad": None, "q1": None, "q3": None, "iqr": None}
    centre = Decimal(median(ordered))
    mad = Decimal(median([abs(value - centre) for value in ordered]))
    q1, q3 = percentile(ordered, .25), percentile(ordered, .75)
    return {"count": len(ordered), "median": centre, "mad": mad, "q1": q1, "q3": q3,
            "iqr": q3 - q1 if q1 is not None and q3 is not None else None}


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def empirical_bayes_rate(successes: int, total: int, prior_successes: int, prior_total: int) -> float | None:
    if total < 0 or prior_total <= 0:
        return None
    alpha = max(1.0, float(prior_successes))
    beta = max(1.0, float(prior_total - prior_successes))
    return (successes + alpha) / (total + alpha + beta)


def provider_graph(claims: Iterable[object], network_id: str, max_nodes: int = 120, max_edges: int = 240) -> dict:
    """Build a bounded explicit-network graph without changing full-population metrics."""
    rows = [row for row in claims if getattr(row, "network_id", None) == network_id]
    providers: dict[str, dict] = {}
    members: dict[str, dict] = {}
    edge_groups: dict[tuple[str, str], dict] = {}
    for claim in rows:
        provider = claim.provider_token; member = claim.member_token
        p = providers.setdefault(provider, {"id": f"provider:{provider}", "key": provider, "type": "provider", "claims": 0, "amount": Decimal("0")})
        p["claims"] += 1; p["amount"] += Decimal(claim.net_amount)
        m = members.setdefault(member, {"id": f"member:{member}", "key": member, "type": "member", "claims": 0})
        m["claims"] += 1
        edge = edge_groups.setdefault((provider, member), {"claim_ids": set(), "amount": Decimal("0")})
        edge["claim_ids"].add(claim.id); edge["amount"] += Decimal(claim.net_amount)
    provider_limit = min(len(providers), max(1, max_nodes // 2))
    visible_providers = {item[0] for item in sorted(providers.items(), key=lambda item: (-item[1]["claims"], item[0]))[:provider_limit]}
    eligible_members: dict[str, int] = defaultdict(int)
    for provider, member in edge_groups:
        if provider in visible_providers: eligible_members[member] += members[member]["claims"]
    member_limit = max(0, max_nodes - len(visible_providers))
    visible_members = {item[0] for item in sorted(eligible_members.items(), key=lambda item: (-item[1], item[0]))[:member_limit]}
    edge_keys = [(p, m) for p, m in edge_groups if p in visible_providers and m in visible_members]
    edge_keys.sort(key=lambda key: (-len(edge_groups[key]["claim_ids"]), key))
    edges = []
    for provider, member in edge_keys[:max_edges]:
        edge = edge_groups[(provider, member)]
        edges.append({"id": f"provider:{provider}|member:{member}", "source": f"provider:{provider}", "target": f"member:{member}",
                      "type": "treated_member", "claim_count": len(edge["claim_ids"]),
                      "associated_amount": str(edge["amount"]), "claim_ids": sorted(edge["claim_ids"])})
    connected = {endpoint for edge in edges for endpoint in (edge["source"], edge["target"])}
    nodes = [{**node, "amount": str(node.get("amount", 0))} for node in providers.values() if node["id"] in connected]
    nodes += [node for node in members.values() if node["id"] in connected]
    total_nodes = len(providers) + len(members); total_edges = len(edge_groups)
    distinct_amount = sum((Decimal(row.net_amount) for row in {row.id: row for row in rows}.values()), Decimal("0"))
    total_claims = len({row.id for row in rows})
    provider_ranking = sorted(providers.values(), key=lambda item: (-item["claims"], -item["amount"], item["key"]))
    member_providers: dict[str, set[str]] = defaultdict(set)
    for provider, member in edge_groups:
        member_providers[member].add(provider)
    shared_members = sorted(({"member": member, "provider_count": len(keys), "claims": members[member]["claims"]}
                             for member, keys in member_providers.items() if len(keys) > 1),
                            key=lambda item: (-item["provider_count"], -item["claims"], item["member"]))
    provider_shares = [item["claims"] / total_claims for item in providers.values()] if total_claims else []
    hhi = sum(share * share for share in provider_shares)
    top_share = provider_ranking[0]["claims"] / total_claims if provider_ranking and total_claims else 0
    concentration = "high" if hhi >= .25 else "moderate" if hhi >= .15 else "distributed"
    return {"network_id": network_id, "nodes": nodes, "edges": edges, "metrics": {"node_count": len(nodes), "edge_count": len(edges),
            "total_node_count": total_nodes, "total_edge_count": total_edges,
            "provider_count": len(providers), "member_count": len(members), "multi_provider_members": len(shared_members),
            "distinct_claims": total_claims, "distinct_associated_amount": str(distinct_amount),
            "top_provider_claim_share": round(top_share, 4), "provider_hhi": round(hhi, 4),
            "concentration": concentration},
            "insights": {"top_providers": [{**item, "amount": str(item["amount"])} for item in provider_ranking[:10]],
                "shared_members": shared_members[:10], "strongest_relationships": edges[:10],
                "interpretation": [
                    "A provider node connects to a member only when committed claims show that provider treated that member.",
                    "A thicker relationship means more distinct claims between that provider and member; it is not proof of coordination.",
                    f"Provider claim concentration is {concentration} (HHI {hhi:.3f}); use the ranked evidence below to decide where to review.",
                    f"{len(shared_members)} members appear across more than one provider in this administrative network.",
                ]},
            "truncated": len(nodes) < total_nodes or len(edges) < total_edges,
            "boundary": "Claims sharing the supplied administrative network/TPA identifier",
            "provenance": "Observed provider-member relationships derived from committed canonical claims; no inferred links"}
