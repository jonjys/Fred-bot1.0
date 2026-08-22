import { NextResponse } from "next/server";
import { getLiveStatus } from "../../lib/getSummary";

export const dynamic = "force-dynamic";

export async function GET() {
  const url = process.env.LIVE_TELEMETRY_URL;
  const token = process.env.LIVE_TELEMETRY_TOKEN;
  if (!url) return NextResponse.json(getLiveStatus(), { headers: { "Cache-Control": "no-store" } });
  try {
    const response = await fetch(url, { cache: "no-store", headers: token ? { Authorization: `Bearer ${token}` } : {}, signal: AbortSignal.timeout(4000) });
    if (!response.ok) throw new Error(`telemetry ${response.status}`);
    return NextResponse.json(await response.json(), { headers: { "Cache-Control": "no-store" } });
  } catch {
    return NextResponse.json(getLiveStatus(), { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
