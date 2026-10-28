/**
 * Normalize a pathname from Qoder Sites / Kong / local Vite into an app route.
 * The platform may pass the public path, strip `/functions/v1/<name>`, or keep
 * only the function name (`/app/...`). Trailing slashes are not significant.
 *
 * @param {string} pathname
 * @returns {string}
 */
export function normalizeApiPath(pathname) {
  let path = String(pathname ?? "/");
  const hash = path.indexOf("#");
  if (hash >= 0) path = path.slice(0, hash);
  const query = path.indexOf("?");
  if (query >= 0) path = path.slice(0, query);
  try {
    path = decodeURI(path);
  } catch {
    // Keep the raw pathname when it is not valid percent-encoding.
  }
  path = path.replace(/\/{2,}/g, "/");
  if (!path.startsWith("/")) path = `/${path}`;

  const apiAt = path.indexOf("/api/");
  if (apiAt > 0) path = path.slice(apiAt);

  const prefixes = ["/functions/v1/app", "/functions/v1", "/v1/app", "/app"];
  for (let guard = 0; guard < 6; guard += 1) {
    let stripped = false;
    for (const prefix of prefixes) {
      if (path === prefix || path.startsWith(`${prefix}/`)) {
        path = path.slice(prefix.length) || "/";
        if (!path.startsWith("/")) path = `/${path}`;
        stripped = true;
      }
    }
    if (!stripped) break;
  }

  if (path.length > 1 && path.endsWith("/")) path = path.slice(0, -1);
  if (path === "") path = "/";

  if (path !== "/" && !path.startsWith("/api/")) {
    for (const route of API_ROUTES) {
      if (route !== "/" && (path === route || path.endsWith(route))) {
        path = route;
        break;
      }
    }
  }
  return path;
}

/** Longer routes first so suffix matching does not collapse `/api/foods/search`. */
export const API_ROUTES = [
  "/",
  "/api/services/status",
  "/api/foods/search",
  "/api/foods/random",
  "/api/user/preferences",
  "/api/user/history/clear",
  "/api/user/history",
  "/api/categories",
  "/api/feedback",
  "/api/foods",
];

/**
 * @param {string} pathname
 * @returns {boolean}
 */
export function isKnownRoute(pathname) {
  return API_ROUTES.includes(pathname);
}
