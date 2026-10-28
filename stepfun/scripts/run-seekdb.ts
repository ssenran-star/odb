/**
 * Linux loader helper for embedded seekdb.
 * libseekdb.so needs to be preloaded, otherwise dlopen fails with
 * "cannot allocate memory in static TLS block".
 * Ubuntu 24 ships libaio.so.1t64; expose it as libaio.so.1 via LD_LIBRARY_PATH.
 */
import { spawn } from "node:child_process";
import { createRequire } from "node:module";
import { existsSync, mkdirSync, symlinkSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const entry = process.argv[2] ?? "server/index.ts";

async function bindingsDir(): Promise<string> {
  const bindingsRoot = path.dirname(require.resolve("@seekdb/js-bindings"));
  const downloaded = require(path.join(bindingsRoot, "download.js")) as {
    ensureBindingsDownloaded: () => Promise<string>;
  };
  return downloaded.ensureBindingsDownloaded();
}

function libaioPath(): string | null {
  const dir = path.join(root, ".cache", "lib");
  const link = path.join(dir, "libaio.so.1");
  const packaged = [
    "/lib/x86_64-linux-gnu/libaio.so.1",
    "/usr/lib/x86_64-linux-gnu/libaio.so.1",
    "/lib64/libaio.so.1",
  ];
  if (packaged.some((file) => existsSync(file))) return null;
  const t64 = "/lib/x86_64-linux-gnu/libaio.so.1t64";
  if (!existsSync(t64)) {
    console.error("libaio.so.1 is missing. Install libaio1, or libaio1t64 on Ubuntu 24.");
    return null;
  }
  mkdirSync(dir, { recursive: true });
  if (!existsSync(link)) symlinkSync(t64, link);
  return dir;
}

const env = { ...process.env };
if (process.platform === "linux") {
  const aio = libaioPath();
  if (aio) env.LD_LIBRARY_PATH = `${aio}${env.LD_LIBRARY_PATH ? `:${env.LD_LIBRARY_PATH}` : ""}`;
  const dir = await bindingsDir();
  const so = path.join(dir, "libseekdb.so");
  if (existsSync(so) && !env.LD_PRELOAD?.includes("libseekdb.so")) {
    env.LD_PRELOAD = env.LD_PRELOAD ? `${so} ${env.LD_PRELOAD}` : so;
  }
}

const child = spawn(process.execPath, ["--import", "tsx", path.join(root, entry)], {
  cwd: root,
  env,
  stdio: "inherit",
});

function stop(signal: NodeJS.Signals): void {
  child.kill(signal);
}

process.on("SIGINT", () => stop("SIGINT"));
process.on("SIGTERM", () => stop("SIGTERM"));

child.on("exit", (code, signal) => {
  if (signal) {
    process.exit(1);
    return;
  }
  process.exit(code ?? 1);
});
