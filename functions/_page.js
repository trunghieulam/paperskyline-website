// Shared shell for the Functions' own HTML: same stylesheet and fonts as the static pages, never indexed.
export const esc = (s) => String(s).replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);

export function page(status, title, body) {
  return new Response(`<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} | Paper Skyline</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@800&amp;family=Be+Vietnam+Pro:wght@400;600;700&amp;display=swap">
<link rel="stylesheet" href="/styles.css">
</head>
<body>
<main id="main" class="wrap">
${body}
</main>
</body>
</html>
`, { status, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } });
}

// Stub data. Production: shipped cities from the city graph, wishes checked against GeoNames cities15000.
export const SHIPPED = {
  paris: 'Paris', 'new-york': 'New York', tokyo: 'Tokyo', cairo: 'Cairo', 'rio-de-janeiro': 'Rio de Janeiro',
  london: 'London', sydney: 'Sydney', beijing: 'Beijing', rome: 'Rome', toronto: 'Toronto', bangkok: 'Bangkok',
  barcelona: 'Barcelona', 'hong-kong': 'Hong Kong', istanbul: 'Istanbul', 'san-francisco': 'San Francisco',
};
export const VOTES = { paris: 128, tokyo: 96, 'new-york': 71 };
