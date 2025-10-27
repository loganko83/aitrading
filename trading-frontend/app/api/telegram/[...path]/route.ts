/**
 * Telegram Notification API Proxy
 * Handles: /api/telegram/*
 * Proxies to: backend /api/v1/telegram/*
 */

import { NextRequest } from 'next/server';
import { proxyToBackend } from '@/lib/api/proxy';

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/telegram${path}`);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/telegram${path}`);
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/telegram${path}`);
}
