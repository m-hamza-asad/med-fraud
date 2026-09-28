export type User = { username: string; role: 'admin' | 'analyst' }
export type Claim = { id: number; claim_id: string; member: string; provider: string; network_id?: string; claim_type: string; service_date: string; submitted_amount: string; net_amount: string; paid_amount: string; decision: 'Flagged' | 'No flag detected' | 'Not evaluated'; coverage: 'Complete' | 'Partial' | 'Not evaluated'; primary_reason: string; triggered_rules: number; evaluation_run_id?: number }

let csrf = sessionStorage.getItem('csrf') ?? ''
export function setCsrf(value: string) { csrf = value; sessionStorage.setItem('csrf', value) }

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { credentials: 'include', ...init, headers: { ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...(csrf ? { 'x-csrf-token': csrf } : {}), ...init.headers } })
  if (!response.ok) { const body = await response.json().catch(() => ({ detail: 'Request failed' })); throw new Error(body.detail ?? 'Request failed') }
  return response.json() as Promise<T>
}

