/**
 * Telegram Notification API Client
 *
 * Telegram bot integration for trading notifications
 */

import { apiPost, apiGet, apiDelete } from './client';

// ==================== Types ====================

export interface TelegramRegisterRequest {
  telegram_chat_id: string;
}

export interface TelegramSettings {
  user_id: string;
  telegram_chat_id: string;
  is_active: boolean;
}

export interface TelegramTestResponse {
  success: boolean;
  message: string;
  chat_id: string;
}

// ==================== API Functions ====================

/**
 * Register Telegram chat ID for notifications
 */
export async function registerTelegram(
  data: TelegramRegisterRequest,
  token: string
): Promise<TelegramSettings> {
  return apiPost<TelegramSettings>(
    '/telegram/register',
    data,
    token
  );
}

/**
 * Get current Telegram settings
 */
export async function getTelegramSettings(
  token: string
): Promise<TelegramSettings> {
  return apiGet<TelegramSettings>('/telegram/settings', token);
}

/**
 * Delete Telegram settings
 */
export async function deleteTelegramSettings(
  token: string
): Promise<{ success: boolean; message: string }> {
  return apiDelete<{ success: boolean; message: string }>(
    '/telegram/settings',
    token
  );
}

/**
 * Send test notification
 */
export async function sendTestNotification(
  token: string
): Promise<TelegramTestResponse> {
  return apiPost<TelegramTestResponse>(
    '/telegram/test',
    undefined,
    token
  );
}

export default {
  registerTelegram,
  getTelegramSettings,
  deleteTelegramSettings,
  sendTestNotification,
};
