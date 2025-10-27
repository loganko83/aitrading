/**
 * Wallet Transfer API Proxy
 * Handles: /api/wallet/*
 * Proxies to: backend /api/v1/wallet/*
 */

import { NextRequest } from 'next/server';
import { proxyToBackend } from '@/lib/api/proxy';

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/wallet${path}`);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/wallet${path}`);
}
