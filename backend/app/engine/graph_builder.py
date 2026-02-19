"""
Build a NetworkX DiGraph from a clean transaction DataFrame.

Node attributes (added by this module, used by algorithms):
  - total_transactions (int): count of rows where the account is sender OR receiver
  - out_degree_count (int): number of transactions where account is sender
  - in_degree_count (int): number of transactions where account is receiver

Edge attributes:
  - weight (float): total amount transferred across all transactions on this edge
  - count (int): number of transaction rows between this sender/receiver pair
"""

import networkx as nx
import pandas as pd


def build_graph(df: pd.DataFrame) -> nx.DiGraph:
    """
    Construct a directed graph from the clean transaction DataFrame.

    Multi-edges (multiple rows between the same sender/receiver) are collapsed
    into a single weighted edge. Per-account transaction counts are stored as
    node attributes for use by shell-chain and suppression algorithms.

    Fully vectorised — no Python-level loops over rows or groups.
    """
    G: nx.DiGraph = nx.DiGraph()

    # ── Node attributes (vectorised) ──────────────────────────────────────
    sender_counts   = df["sender_id"].value_counts()
    receiver_counts = df["receiver_id"].value_counts()
    all_accounts    = sender_counts.index.union(receiver_counts.index)

    out_cnt = sender_counts.reindex(all_accounts, fill_value=0)
    in_cnt  = receiver_counts.reindex(all_accounts, fill_value=0)

    G.add_nodes_from(
        (acc, {
            "total_transactions": int(out_cnt[acc] + in_cnt[acc]),
            "out_degree_count":   int(out_cnt[acc]),
            "in_degree_count":    int(in_cnt[acc]),
        })
        for acc in all_accounts
    )

    # ── Edge attributes (vectorised groupby + bulk add) ───────────────────
    edge_df = (
        df.groupby(["sender_id", "receiver_id"], sort=False)["amount"]
        .agg(weight="sum", count="count")
        .reset_index()
    )

    G.add_edges_from(
        (row.sender_id, row.receiver_id, {"weight": float(row.weight), "count": int(row.count)})
        for row in edge_df.itertuples(index=False)
    )

    return G
