/**
 * Webhooks API Proxy
 * Proxies webhook management requests to backend
 */

import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/api/proxy";

export async function GET(request: NextRequest) {
  return proxyToBackend(request, "/webhook");
}

export async function POST(request: NextRequest) {
  return proxyToBackend(request, "/webhook");
}

export async function PUT(request: NextRequest) {
  return proxyToBackend(request, "/webhook");
}

export async function DELETE(request: NextRequest) {
  return proxyToBackend(request, "/webhook");
}
