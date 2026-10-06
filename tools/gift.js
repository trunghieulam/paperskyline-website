(function () {
  var lines = document.querySelectorAll('[data-gift-line]');
  var box = document.querySelector('[data-gift-url]');
  if (!lines.length || !box || !window.fetch) return;
  fetch(box.getAttribute('data-gift-url'), { credentials: 'omit', cache: 'no-store', referrerPolicy: 'no-referrer' })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
    .then(function (d) {
      var cap = Number(d.cap), left = Number(d.remaining), end = Date.parse(d.ends);
      if (!(cap > 0) || !(left >= 0)) return;
      var n = function (v) { return v.toLocaleString('en-GB'); };
      var state = end < Date.now() ? 'ended' : left === 0 ? 'out' : 'open';
      var text = state === 'ended' ? 'This gift has ended' : state === 'out' ? 'All ' + n(cap) + ' gifts are claimed' : n(Math.min(left, cap)) + ' of ' + n(cap) + ' left';
      lines.forEach(function (el) { el.textContent = text; });
      document.querySelectorAll('[data-gift]').forEach(function (el) { el.setAttribute('data-state', state); });
    })
    .catch(function () {});
})();
