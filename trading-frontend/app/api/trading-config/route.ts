import { NextRequest, NextResponse } from "next/server";
import { proxyToBackend } from "@/lib/api/proxy";

export async function GET(request: NextRequest) {
  return proxyToBackend(request, "/trading-config");
}

export async function POST(request: NextRequest) {
  return proxyToBackend(request, "/trading-config");
}

export async function PUT(request: NextRequest) {
  return proxyToBackend(request, "/trading-config");
}

export async function DELETE(request: NextRequest) {
  return proxyToBackend(request, "/trading-config");
}
