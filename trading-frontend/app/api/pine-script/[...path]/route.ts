/**
 * Pine Script API Proxy
 * Handles: /api/pine-script/*
 * Proxies to: backend /api/v1/pine-script/* (KEEP HYPHEN)
 */

import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/api/proxy";

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join("/")}` : "";
  return proxyToBackend(request, `/pine-script${path}`);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join("/")}` : "";
  return proxyToBackend(request, `/pine-script${path}`);
}
