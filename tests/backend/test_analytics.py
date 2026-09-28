from decimal import Decimal
from types import SimpleNamespace

from medfraud.analytics import empirical_bayes_rate, percentile, provider_graph, robust_summary, wilson_interval


def test_robust_distribution_and_sparse_rate_methods():
    values = [Decimal(str(value)) for value in (1, 2, 3, 4, 100)]
    assert percentile(values, .5) == 3
    summary = robust_summary(values)
    assert summary["median"] == 3 and summary["mad"] == 1
    low, high = wilson_interval(5, 10)
    assert low is not None and low < .5 < high
    assert empirical_bayes_rate(1, 2, 10, 100) < .5


def test_graph_respects_explicit_boundary_and_deduplicates_claim_amounts():
    rows = [
        SimpleNamespace(id=1, network_id="N1", provider_token="P1", member_token="M1", net_amount=Decimal("10")),
        SimpleNamespace(id=2, network_id="N1", provider_token="P2", member_token="M1", net_amount=Decimal("20")),
        SimpleNamespace(id=3, network_id="N2", provider_token="P3", member_token="M1", net_amount=Decimal("999")),
    ]
    graph = provider_graph(rows, "N1")
    assert graph["metrics"]["distinct_associated_amount"] == "30"
    assert graph["metrics"]["distinct_claims"] == 2
    assert graph["metrics"]["multi_provider_members"] == 1
    assert graph["metrics"]["provider_count"] == 2
    assert graph["insights"]["shared_members"][0]["member"] == "M1"
    assert "not proof" in graph["insights"]["interpretation"][1]
    assert {node["key"] for node in graph["nodes"]} == {"P1", "P2", "M1"}


def test_graph_bounds_rendered_payload_but_keeps_population_metrics():
    rows = [SimpleNamespace(id=i, network_id="N1", provider_token=f"P{i}", member_token=f"M{i}", net_amount=Decimal("10")) for i in range(20)]
    graph = provider_graph(rows, "N1", max_nodes=10, max_edges=4)
    assert graph["truncated"] is True
    assert len(graph["nodes"]) <= 10 and len(graph["edges"]) <= 4
    assert graph["metrics"]["total_node_count"] == 40
    assert graph["metrics"]["total_edge_count"] == 20
    assert graph["metrics"]["distinct_claims"] == 20
    assert graph["metrics"]["distinct_associated_amount"] == "200"
