/**
 * CloudShare — Cloudflare Containers worker
 *
 * Architecture:
 *   - BackendContainer  : Durable Object that manages the FastAPI container
 *   - FrontendContainer : Durable Object that manages the nginx/React container
 *
 * Request routing:
 *   /api/*  → BackendContainer  (FastAPI on port 8000)
 *   /*      → FrontendContainer (nginx on port 80)
 *
 * Each DO class uses a singleton stub keyed on a fixed string so all requests
 * reach the same container instance.
 */

import { DurableObject } from "cloudflare:workers";

// ── Backend DO ────────────────────────────────────────────────────────────────
export class BackendContainer extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    // Start the container when the DO is first created
    this.ctx.container.start();
  }

  async fetch(request) {
    // Forward to the container; it listens on port 8000
    return this.ctx.container.fetch(request);
  }
}

// ── Frontend DO ───────────────────────────────────────────────────────────────
export class FrontendContainer extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.ctx.container.start();
  }

  async fetch(request) {
    // Forward to nginx; it listens on port 80
    return this.ctx.container.fetch(request);
  }
}

// ── Worker entry point ────────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      // Route to backend container via its singleton DO
      const id = env.BACKEND.idFromName("backend-singleton");
      const stub = env.BACKEND.get(id);
      return stub.fetch(request);
    }

    // Route everything else to the frontend container
    const id = env.FRONTEND.idFromName("frontend-singleton");
    const stub = env.FRONTEND.get(id);
    return stub.fetch(request);
  },
};
