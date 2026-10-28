export interface PowerContextSettings {
  baseUrl: string;
  scopeId: string;
  token?: string;
}

export interface SeekDbSettings {
  host: string;
  port: number;
  user: string;
  password: string;
  database: string;
}

export interface ServiceConfig {
  powerContext: PowerContextSettings | null;
  seekdb: SeekDbSettings | null;
}

const FORCE_OFF = new Set(["0", "false", "no", "off"]);

function read(raw: Record<string, string | undefined>, key: string): string {
  return (raw[key] ?? "").trim();
}

/**
 * Real clients turn on when their env vars are present.
 * `USE_REAL_SERVICES=false` forces the in-process demo even if URLs are set.
 * `USE_REAL_SERVICES=true` does not invent hosts that were left blank.
 */
export function serviceConfigFrom(raw: Record<string, string | undefined>): ServiceConfig {
  const forcedOff = FORCE_OFF.has(read(raw, "USE_REAL_SERVICES").toLowerCase());
  const baseUrl = read(raw, "POWERCONTEXT_URL").replace(/\/+$/, "");
  const scopeId = read(raw, "POWERCONTEXT_SCOPE_ID");
  const token = read(raw, "POWERCONTEXT_API_TOKEN");
  const host = read(raw, "SEEKDB_HOST");
  const parsedPort = Number.parseInt(read(raw, "SEEKDB_PORT") || "2881", 10);
  const port = Number.isFinite(parsedPort) && parsedPort > 0 ? parsedPort : 2881;

  return {
    powerContext: !forcedOff && baseUrl && scopeId
      ? { baseUrl, scopeId, token: token || undefined }
      : null,
    seekdb: !forcedOff && host
      ? {
        host,
        port,
        user: read(raw, "SEEKDB_USER") || "root",
        password: read(raw, "SEEKDB_PASSWORD"),
        database: read(raw, "SEEKDB_DATABASE") || "food_app",
      }
      : null,
  };
}

export const SERVICE_ENV_KEYS = [
  "USE_REAL_SERVICES",
  "POWERCONTEXT_URL",
  "POWERCONTEXT_SCOPE_ID",
  "POWERCONTEXT_API_TOKEN",
  "SEEKDB_HOST",
  "SEEKDB_PORT",
  "SEEKDB_USER",
  "SEEKDB_PASSWORD",
  "SEEKDB_DATABASE",
] as const;
