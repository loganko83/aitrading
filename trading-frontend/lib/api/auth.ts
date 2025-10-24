/**
 * Authentication API Client
 *
 * All authentication-related API calls to FastAPI backend
 */

import { apiPost, apiGet } from './client';

// ==================== Types ====================

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string;
}

export interface RegisterResponse {
  success: boolean;
  message: string;
  user_id: string;
  email: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  totp_code?: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  user_id: string;
  email: string;
  requires_2fa: boolean;
  access_token?: string;
  refresh_token?: string;
  token_type: string;
}

export interface Setup2FAResponse {
  success: boolean;
  message: string;
  qr_code_base64: string;
  provisioning_uri: string;
  encrypted_secret: string;
  instructions: string[];
}

export interface Verify2FARequest {
  totp_code: string;
}

export interface Verify2FAResponse {
  success: boolean;
  message: string;
  is_2fa_enabled: boolean;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  success: boolean;
  message: string;
  access_token: string;
  token_type: string;
}

export interface LogoutRequest {
  refresh_token?: string;
}

export interface LogoutResponse {
  success: boolean;
  message: string;
}

export interface CurrentUserResponse {
  user_id: string;
  email: string;
  name?: string;
  is_2fa_enabled: boolean;
  is_active: boolean;
  created_at?: string;
}

// ==================== API Functions ====================

/**
 * Register a new user
 */
export async function register(
  data: RegisterRequest
): Promise<RegisterResponse> {
  return apiPost<RegisterResponse>('/auth/register', data);
}

/**
 * Login user
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  return apiPost<LoginResponse>('/auth/login', data);
}

/**
 * Setup 2FA for current user
 */
export async function setup2FA(token: string): Promise<Setup2FAResponse> {
  return apiPost<Setup2FAResponse>('/auth/2fa/setup', undefined, token);
}

/**
 * Verify 2FA setup
 */
export async function verify2FA(
  data: Verify2FARequest,
  token: string
): Promise<Verify2FAResponse> {
  return apiPost<Verify2FAResponse>('/auth/2fa/verify', data, token);
}

/**
 * Disable 2FA
 */
export async function disable2FA(
  data: Verify2FARequest,
  token: string
): Promise<Verify2FAResponse> {
  return apiPost<Verify2FAResponse>('/auth/2fa/disable', data, token);
}

/**
 * Refresh access token
 */
export async function refreshToken(
  data: RefreshTokenRequest
): Promise<RefreshTokenResponse> {
  return apiPost<RefreshTokenResponse>('/auth/refresh', data);
}

/**
 * Logout user
 */
export async function logout(data?: LogoutRequest): Promise<LogoutResponse> {
  return apiPost<LogoutResponse>('/auth/logout', data);
}

/**
 * Get current user info
 */
export async function getCurrentUser(
  token: string
): Promise<CurrentUserResponse> {
  return apiGet<CurrentUserResponse>('/auth/me', token);
}

export default {
  register,
  login,
  setup2FA,
  verify2FA,
  disable2FA,
  refreshToken,
  logout,
  getCurrentUser,
};
