/**
 * Strategy Configs API Proxy
 * Handles: /api/strategy-configs
 * Proxies to: backend /api/v1/strategies/configs/my
 */

import { NextRequest } from 'next/server';
import { proxyToBackend } from '@/lib/api/proxy';

export async function GET(request: NextRequest) {
  // Route to backend strategies configs endpoint
  return proxyToBackend(request, '/strategies/configs/my');
}
