import { esc, SHIPPED, VOTES } from '../_page.js';

// Spike: the static city page with a live vote count, at the same depth so its relative links still resolve.
export async function onRequestGet({ request, params, env }) {
  const id = params.city;
  if (!SHIPPED[id]) {
    const missing = await env.ASSETS.fetch(new URL('/404.html', request.url));
    return new Response(missing.body, { status: 404, headers: missing.headers });
  }
  const res = await env.ASSETS.fetch(new URL(`/cities/${id}/`, request.url));
  const n = VOTES[id] || 0;
  const out = new HTMLRewriter()
    .on('h1#hero-title', { element: (h1) => h1.after(`<p class="votes">${n} ${n === 1 ? 'player wants' : 'players want'} more of ${esc(SHIPPED[id])}</p>`, { html: true }) })
    .transform(res);
  const headers = new Headers(out.headers);
  headers.set('x-robots-tag', 'noindex');
  headers.set('cache-control', 'public, max-age=60');
  return new Response(out.body, { status: out.status, headers });
}
