/**
 * Performance API Proxy
 * Handles: /api/performance
 * Proxies to: backend /api/v1/performance/performance/summary (double performance!)
 */

import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/api/proxy";

export async function GET(request: NextRequest) {
  // Backend endpoint has double performance: /api/v1/performance/performance/summary
  return proxyToBackend(request, "/performance/performance/summary");
}
