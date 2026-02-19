from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    frontend_url: str = "http://localhost:3000"
    max_upload_size_mb: int = 5

    # ── Result Store ──────────────────────────────────────────────────────────
    result_store_ttl_seconds: int = 3600
    result_store_max_items: int = 10

    # ── Algorithm: Cycle Detection ────────────────────────────────────────────
    min_cycle_length: int = 3
    max_cycle_length: int = 5
    # Cycles whose total edge weight is below (threshold_pct × median_amount × length)
    # are discarded as noise.
    cycle_volume_threshold_pct: float = 0.01

    # ── Algorithm: Smurfing ───────────────────────────────────────────────────
    smurfing_window_hours: int = 72
    smurfing_min_degree: int = 10

    # ── Algorithm: Shell Chain ────────────────────────────────────────────────
    shell_max_total_transactions: int = 3
    shell_chain_min_hops: int = 3

    # ── Algorithm: Velocity ───────────────────────────────────────────────────
    burst_window_hours: int = 1
    burst_min_transactions: int = 5
    daily_velocity_window_hours: int = 24
    daily_velocity_min_transactions: int = 15
    velocity_spike_ratio: float = 3.0
    velocity_spike_window_days: int = 7
    dormancy_min_days: int = 30
    dormancy_activity_window_hours: int = 48
    dormancy_activity_threshold: int = 5

    # ── Suppression ───────────────────────────────────────────────────────────
    # Payroll: flag fan-out accounts whose outgoing transactions are highly regular.
    # CV = std / mean. Low CV ⟹ very consistent ⟹ payroll / automated disbursement.
    payroll_interval_cv_threshold: float = 0.2
    payroll_amount_cv_threshold: float = 0.15
    # Merchant: flag fan-in accounts with high in-degree and no reciprocal flows.
    merchant_min_in_degree: int = 50

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Accounts with a final score below this threshold are excluded from output.
    # With continuous scoring (max 85), 12.0 allows accounts that trigger
    # a detection algorithm to appear even when at the minimum signal strength.
    suspicious_score_threshold: float = 12.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow extra env vars in the file without raising validation errors.
        extra="ignore",
    )


# Module-level singleton — import this everywhere.
settings = Settings()
