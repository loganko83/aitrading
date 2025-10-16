import crypto from 'crypto';

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;
const SALT_LENGTH = 64;
const TAG_LENGTH = 16;
const KEY_LENGTH = 32;
const ITERATIONS = 100000;

/**
 * Derives a key from the encryption key using PBKDF2
 */
function deriveKey(encryptionKey: string, salt: Buffer): Buffer {
  return crypto.pbkdf2Sync(
    encryptionKey,
    salt,
    ITERATIONS,
    KEY_LENGTH,
    'sha512'
  );
}

/**
 * Encrypts text using AES-256-GCM
 * @param text - Plain text to encrypt
 * @param encryptionKey - Base encryption key (from environment)
 * @returns Encrypted string in format: salt:iv:encrypted:tag (all hex encoded)
 */
export function encrypt(text: string, encryptionKey: string): string {
  try {
    // Generate random salt and IV
    const salt = crypto.randomBytes(SALT_LENGTH);
    const iv = crypto.randomBytes(IV_LENGTH);

    // Derive key from encryption key and salt
    const key = deriveKey(encryptionKey, salt);

    // Create cipher
    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);

    // Encrypt
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    // Get authentication tag
    const tag = cipher.getAuthTag();

    // Combine salt, iv, encrypted data, and tag
    return `${salt.toString('hex')}:${iv.toString('hex')}:${encrypted}:${tag.toString('hex')}`;
  } catch (error) {
    throw new Error('Encryption failed');
  }
}

/**
 * Decrypts text encrypted with encrypt()
 * @param encryptedText - Encrypted string in format: salt:iv:encrypted:tag
 * @param encryptionKey - Base encryption key (from environment)
 * @returns Decrypted plain text
 */
export function decrypt(encryptedText: string, encryptionKey: string): string {
  try {
    // Split the encrypted text
    const parts = encryptedText.split(':');
    if (parts.length !== 4) {
      throw new Error('Invalid encrypted text format');
    }

    const salt = Buffer.from(parts[0], 'hex');
    const iv = Buffer.from(parts[1], 'hex');
    const encrypted = parts[2];
    const tag = Buffer.from(parts[3], 'hex');

    // Derive the same key
    const key = deriveKey(encryptionKey, salt);

    // Create decipher
    const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
    decipher.setAuthTag(tag);

    // Decrypt
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  } catch (error) {
    throw new Error('Decryption failed');
  }
}

/**
 * Masks an API key for display (shows first 8 and last 4 characters)
 */
export function maskApiKey(apiKey: string): string {
  if (apiKey.length <= 12) {
    return apiKey;
  }
  const first = apiKey.slice(0, 8);
  const last = apiKey.slice(-4);
  const masked = '*'.repeat(Math.max(apiKey.length - 12, 4));
  return `${first}${masked}${last}`;
}

/**
 * Validates Binance API key format
 */
export function validateBinanceApiKey(apiKey: string): boolean {
  // Binance API keys are 64 characters long and alphanumeric
  return /^[A-Za-z0-9]{64}$/.test(apiKey);
}

/**
 * Validates Binance API secret format
 */
export function validateBinanceApiSecret(apiSecret: string): boolean {
  // Binance API secrets are 64 characters long and alphanumeric
  return /^[A-Za-z0-9]{64}$/.test(apiSecret);
}
