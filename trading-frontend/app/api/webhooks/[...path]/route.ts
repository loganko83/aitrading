/**
 * Webhooks API Catch-all Proxy
 * Handles dynamic paths like /webhooks/{id}
 */

import { NextRequest } from "next/server";
import { proxyToBackend } from "@/lib/api/proxy";

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join("/")}` : "";
  return proxyToBackend(request, `/webhook${path}`);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join("/")}` : "";
  return proxyToBackend(request, `/webhook${path}`);
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join("/")}` : "";
  return proxyToBackend(request, `/webhook${path}`);
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join("/")}` : "";
  return proxyToBackend(request, `/webhook${path}`);
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join("/")}` : "";
  return proxyToBackend(request, `/webhook${path}`);
}
