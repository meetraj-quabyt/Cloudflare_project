/**
 * Cloudflare Worker — CloudShare container router
 *
 * Routes requests to the appropriate container:
 *   /api/*  → backend container (FastAPI on port 8000)
 *   /*      → frontend container (nginx on port 80)
 *
 * The binding names ("backend", "frontend") match the `name` fields
 * in the [[containers]] sections of wrangler.toml.
 */
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      return env.backend.fetch(request);
    }

    return env.frontend.fetch(request);
  },
};
