import { serviceConfigFrom } from "./service-config.ts";

Deno.test("real mode follows env presence and the explicit off switch", () => {
  const empty = serviceConfigFrom({});
  if (empty.powerContext || empty.seekdb) throw new Error("blank env must stay demo");

  const forced = serviceConfigFrom({ USE_REAL_SERVICES: "true" });
  if (forced.powerContext || forced.seekdb) throw new Error("true without hosts must stay demo");

  const pc = serviceConfigFrom({
    POWERCONTEXT_URL: "https://example.trycloudflare.com/",
    POWERCONTEXT_SCOPE_ID: "scp_example",
    POWERCONTEXT_API_TOKEN: "secret-token",
  });
  if (pc.powerContext?.baseUrl !== "https://example.trycloudflare.com") throw new Error("slash");
  if (pc.powerContext.scopeId !== "scp_example") throw new Error("scope");
  if (pc.powerContext.token !== "secret-token") throw new Error("token");
  if (pc.seekdb) throw new Error("seekdb should stay off");

  const off = serviceConfigFrom({
    USE_REAL_SERVICES: "false",
    POWERCONTEXT_URL: "https://example.trycloudflare.com",
    POWERCONTEXT_SCOPE_ID: "scp_example",
    SEEKDB_HOST: "127.0.0.1",
  });
  if (off.powerContext || off.seekdb) throw new Error("false must force demo");

  const seek = serviceConfigFrom({ SEEKDB_HOST: "db.internal", SEEKDB_PORT: "2881" });
  if (!seek.seekdb || seek.seekdb.host !== "db.internal" || seek.seekdb.port !== 2881) {
    throw new Error("seekdb host");
  }
});
