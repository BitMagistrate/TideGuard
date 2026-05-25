export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function bboxToString(bbox: [number, number, number, number]): string {
  const [lonMin, latMin, lonMax, latMax] = bbox;
  return `${lonMin},${latMin},${lonMax},${latMax}`;
}

export function clampHorizon(days: number): number {
  return Math.max(1, Math.min(14, Math.round(days)));
}

export async function fetchForecast(bbox: [number, number, number, number], horizon = 7) {
  const res = await fetch(`${API_URL}/forecast?bbox=${bboxToString(bbox)}&horizon=${clampHorizon(horizon)}`);
  if (!res.ok) throw new Error(`forecast failed: ${res.status}`);
  return res.json();
}

export function clampQuantile(q: number): number {
  if (!Number.isFinite(q)) return 0.9;
  return Math.min(0.99, Math.max(0.5, q));
}

export type ExceedanceCell = {
  lat: number;
  lng: number;
  probability: number;
};

export type ExceedanceResponse = {
  model_version: string;
  bbox: [number, number, number, number];
  horizon_days: number;
  threshold: number;
  quantile: number;
  n_members: number;
  cells: ExceedanceCell[];
};

export async function fetchExceedance(
  bbox: [number, number, number, number],
  horizon = 7,
  quantile = 0.9,
): Promise<ExceedanceResponse> {
  const params = new URLSearchParams({
    bbox: bboxToString(bbox),
    horizon: String(clampHorizon(horizon)),
    quantile: String(clampQuantile(quantile)),
  });
  const res = await fetch(`${API_URL}/forecast/exceedance?${params.toString()}`);
  if (!res.ok) throw new Error(`exceedance failed: ${res.status}`);
  return res.json();
}
