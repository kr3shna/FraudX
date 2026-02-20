import { apiUrl } from './axiosClient';

// ── Types (match backend POST /api/analyze response) ────────────────────────
export interface ValidationSummary {
  rows_total: number;
  rows_accepted: number;
  rows_skipped: number;
  skip_reasons: Record<string, number>;
}

export interface SuspiciousAccount {
  account_id: string;
  suspicion_score: number;
  detected_patterns: string[];
  ring_id: string;
}

export interface FraudRing {
  ring_id: string;
  member_accounts: string[];
  pattern_type: string;
  risk_score: number;
}

export interface ForensicSummary {
  total_accounts_analyzed: number;
  suspicious_accounts_flagged: number;
  fraud_rings_detected: number;
  processing_time_seconds: number;
  total_rows?: number;
  total_amount?: number;
}

export interface GraphNode {
  id: string;
  in_degree: number;
  out_degree: number;
  total_transactions: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight?: number;
  count?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ForensicResult {
  suspicious_accounts: SuspiciousAccount[];
  fraud_rings: FraudRing[];
  summary: ForensicSummary;
  graph?: GraphData | null;
}

export interface AnalyzeResponse {
  status: string;
  session_token: string;
  validation_summary: ValidationSummary;
  result: ForensicResult;
}

/** POST /api/analyze — upload CSV and run analysis. */
export async function analyzeCsv(
  file: File,
  cfg?: Record<string, unknown> | null
): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append('file', file);
  if (cfg != null) {
    form.append('cfg', JSON.stringify(cfg));
  }
  const res = await fetch(`${apiUrl}/api/analyze`, {
    method: 'POST',
    body: form,
    // Do not set Content-Type; browser sets multipart/form-data with boundary
  });
  if (!res.ok) {
    const errBody = await res.text();
    let detail: string;
    try {
      const j = JSON.parse(errBody) as { detail?: string | { msg?: string }[] };
      detail = typeof j.detail === 'string' ? j.detail : j.detail?.[0]?.msg ?? errBody;
    } catch {
      detail = errBody || res.statusText;
    }
    throw new Error(detail);
  }
  return res.json() as Promise<AnalyzeResponse>;
}

/** Query params for GET /api/results */
export interface GetResultsParams {
  account_id?: string | null;
  ring_id?: string | null;
  min_score?: number | null;
  pattern?: string | null;
}

/** GET /api/results — retrieve stored analysis by session token. */
export async function getResults(
  sessionToken: string,
  params?: GetResultsParams
): Promise<ForensicResult> {
  const sp = new URLSearchParams();
  if (params?.account_id != null && params.account_id !== '') sp.set('account_id', params.account_id);
  if (params?.ring_id != null && params.ring_id !== '') sp.set('ring_id', params.ring_id);
  if (params?.min_score != null) sp.set('min_score', String(params.min_score));
  if (params?.pattern != null && params.pattern !== '') sp.set('pattern', params.pattern);
  const qs = sp.toString();
  const url = `${apiUrl}/api/results${qs ? `?${qs}` : ''}`;
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      'X-Session-Token': sessionToken,
      Accept: 'application/json',
    },
  });
  if (!res.ok) {
    const errBody = await res.text();
    let detail: string;
    try {
      const j = JSON.parse(errBody) as { detail?: string | { msg?: string }[] };
      detail = typeof j.detail === 'string' ? j.detail : j.detail?.[0]?.msg ?? errBody;
    } catch {
      detail = errBody || res.statusText;
    }
    throw new Error(detail);
  }
  return res.json() as Promise<ForensicResult>;
}
