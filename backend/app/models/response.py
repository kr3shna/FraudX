from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Node in the directed transaction graph (for visualization)."""

    id: str
    in_degree: int = 0
    out_degree: int = 0
    total_transactions: int = 0


class GraphEdge(BaseModel):
    """Directed edge in the transaction graph (source -> target)."""

    source: str
    target: str
    weight: float = 0.0
    count: int = 1


class GraphData(BaseModel):
    """Directed graph structure for frontend visualization."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SuspiciousAccount(BaseModel):
    """A single account flagged as suspicious, with its score and detected patterns."""

    account_id: str
    suspicion_score: float = Field(ge=0.0, le=100.0)
    # Sorted alphabetically — enforced by output_builder, validated here.
    detected_patterns: list[str]
    # "RING_001", "RING_002", ... or "NONE" if not part of any multi-member ring.
    ring_id: str


class FraudRing(BaseModel):
    """A group of accounts linked by overlapping fraud patterns."""

    ring_id: str
    # Sorted alphabetically — enforced by output_builder.
    member_accounts: list[str]
    # "cycle" | "smurfing" | "shell" | "mixed"
    # Determined by the dominant pattern type in the ring.
    pattern_type: str
    risk_score: float = Field(ge=0.0, le=100.0)


class ForensicSummary(BaseModel):
    """High-level statistics for the full analysis run."""

    total_accounts_analyzed: int
    suspicious_accounts_flagged: int
    fraud_rings_detected: int
    processing_time_seconds: float
    total_rows: int = 0
    total_amount: float = 0.0


class ForensicResult(BaseModel):
    """
    The complete forensic analysis output.
    This is the shape of both the API response payload and the downloadable JSON file.

    Ordering guarantees (enforced by output_builder):
      suspicious_accounts → sorted by suspicion_score DESC
      fraud_rings         → sorted by risk_score DESC
      member_accounts     → sorted alphabetically per ring
      detected_patterns   → sorted alphabetically per account
    """

    suspicious_accounts: list[SuspiciousAccount]
    fraud_rings: list[FraudRing]
    summary: ForensicSummary
    # Directed graph for frontend visualization (subgraph of suspicious + connected accounts)
    graph: GraphData | None = None


class ValidationSummary(BaseModel):
    """Row-level parsing statistics returned before algorithm execution."""

    rows_total: int
    rows_accepted: int
    rows_skipped: int
    # e.g. {"duplicate_transaction_id": 3, "invalid_amount": 7}
    skip_reasons: dict[str, int]


class AnalyzeResponse(BaseModel):
    """Full response from POST /api/analyze."""

    status: str
    session_token: str
    validation_summary: ValidationSummary
    result: ForensicResult
