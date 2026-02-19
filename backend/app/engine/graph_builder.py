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
    """
    G: nx.DiGraph = nx.DiGraph()

    # ── Compute per-account totals from the DataFrame ──────────────────────
    sender_counts = df["sender_id"].value_counts()
    receiver_counts = df["receiver_id"].value_counts()
    all_accounts: set[str] = set(df["sender_id"]) | set(df["receiver_id"])

    for acc in all_accounts:
        out_cnt = int(sender_counts.get(acc, 0))
        in_cnt = int(receiver_counts.get(acc, 0))
        G.add_node(
            acc,
            total_transactions=out_cnt + in_cnt,
            out_degree_count=out_cnt,
            in_degree_count=in_cnt,
        )

    # ── Add collapsed edges with aggregate attributes ──────────────────────
    for (sender, receiver), group in df.groupby(["sender_id", "receiver_id"]):
        G.add_edge(
            sender,
            receiver,
            weight=float(group["amount"].sum()),
            count=len(group),
        )

    return G
