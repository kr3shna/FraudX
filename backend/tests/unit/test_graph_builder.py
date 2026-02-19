"""Unit tests for app/engine/graph_builder.py."""

import pandas as pd
import pytest

from app.engine.graph_builder import build_graph


def test_triangle_node_count(triangle_df):
    G = build_graph(triangle_df)
    assert G.number_of_nodes() == 3


def test_triangle_edge_count(triangle_df):
    G = build_graph(triangle_df)
    assert G.number_of_edges() == 3


def test_node_total_transactions(triangle_df):
    G = build_graph(triangle_df)
    # Each node in the triangle sends 1 and receives 1 → total = 2
    for node in ["ACC_A", "ACC_B", "ACC_C"]:
        assert G.nodes[node]["total_transactions"] == 2
        assert G.nodes[node]["out_degree_count"] == 1
        assert G.nodes[node]["in_degree_count"] == 1


def test_edge_weight_is_sum_of_amounts():
    """Two transactions between the same pair → single edge with summed weight."""
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "sender_id":      ["ACC_A", "ACC_A"],
        "receiver_id":    ["ACC_B", "ACC_B"],
        "amount":         [1000.0, 2000.0],
        "timestamp":      pd.to_datetime(["2024-01-01 10:00:00", "2024-01-01 11:00:00"]),
    })
    G = build_graph(df)
    assert G.number_of_edges() == 1
    assert G["ACC_A"]["ACC_B"]["weight"] == 3000.0
    assert G["ACC_A"]["ACC_B"]["count"] == 2


def test_edge_weight_single_transaction(triangle_df):
    G = build_graph(triangle_df)
    assert G["ACC_A"]["ACC_B"]["weight"] == 5000.0
    assert G["ACC_A"]["ACC_B"]["count"] == 1


def test_sender_only_node_has_zero_in_degree():
    df = pd.DataFrame({
        "transaction_id": ["T1"],
        "sender_id":      ["ACC_A"],
        "receiver_id":    ["ACC_B"],
        "amount":         [500.0],
        "timestamp":      pd.to_datetime(["2024-01-01 10:00:00"]),
    })
    G = build_graph(df)
    assert G.nodes["ACC_A"]["in_degree_count"] == 0
    assert G.nodes["ACC_A"]["out_degree_count"] == 1
    assert G.nodes["ACC_B"]["in_degree_count"] == 1
    assert G.nodes["ACC_B"]["out_degree_count"] == 0


def test_all_accounts_present_as_nodes(fan_in_df):
    G = build_graph(fan_in_df)
    all_expected = set(fan_in_df["sender_id"]) | set(fan_in_df["receiver_id"])
    assert set(G.nodes()) == all_expected


def test_graph_is_directed(triangle_df):
    import networkx as nx
    G = build_graph(triangle_df)
    assert isinstance(G, nx.DiGraph)
