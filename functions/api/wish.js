import { esc, page, SHIPPED } from '../_page.js';

// Letters and marks in any script, with the spaces, hyphens, apostrophes and dots city names use.
const NAME = /^[\p{L}\p{M}][\p{L}\p{M} .'’-]{0,58}[\p{L}\p{M}.]$/u;

export async function onRequestPost({ request }) {
  const type = request.headers.get('content-type') || '';
  if (!type.startsWith('application/x-www-form-urlencoded') && !type.startsWith('multipart/form-data')) {
    return page(415, 'Wish not sent', '<h1>That did not look like the wish form</h1><p><a href="/">Back to Paper Skyline</a></p>');
  }
  const form = await request.formData();
  // Honeypot: the field is hidden from people, so only bots fill it in.
  if (form.get('website')) return page(400, 'Wish not sent', '<h1>Wish not sent</h1>');
  const city = String(form.get('city') || '').normalize('NFC').trim().replace(/\s+/g, ' ');
  if (!NAME.test(city)) {
    return page(400, 'Wish not sent', `<h1>Which city?</h1>
<p>Write the city's name, for example Jakarta or Manila, and send it again.</p>
<p><a href="/api/wish">Back to the form</a></p>`);
  }
  const id = Object.keys(SHIPPED).find((k) => SHIPPED[k].toLowerCase() === city.toLowerCase());
  // Production: one row to D1 (city, day, salted IP hash for the rate limit), as the stats Worker does.
  const body = id
    ? `<h1>${esc(SHIPPED[id])} is already in the game</h1><p><a href="/cities/${id}/">Fly over ${esc(SHIPPED[id])}</a></p>`
    : `<h1>Thank you</h1><p>Your wish for <strong>${esc(city)}</strong> is on the list. The cities with the most wishes are painted first.</p><p><a href="/cities/">See the cities you can fly today</a></p>`;
  return page(200, 'Wish sent', body);
}

// Spike only: the form itself. Production puts it on a static wish page.
export const onRequestGet = () => page(200, 'Wish for a city', `<h1>Wish for a city</h1>
<form method="post" action="/api/wish">
  <p><label for="city">City</label> <input id="city" name="city" required maxlength="60" autocomplete="off"></p>
  <p hidden><label for="website">Leave empty</label> <input id="website" name="website" tabindex="-1" autocomplete="off"></p>
  <p><button type="submit">Send my wish</button></p>
</form>`);
