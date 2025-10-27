/**
 * Accounts Secure API Proxy
 * Handles: /api/accounts-secure/*
 * Proxies to: backend /api/v1/accounts-secure/*
 */

import { NextRequest } from 'next/server';
import { proxyToBackend } from '@/lib/api/proxy';

// Handle all HTTP methods
export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/accounts-secure${path}`);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/accounts-secure${path}`);
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/accounts-secure${path}`);
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/accounts-secure${path}`);
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path ? `/${params.path.join('/')}` : '';
  return proxyToBackend(request, `/accounts-secure${path}`);
}
