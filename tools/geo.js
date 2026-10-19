(function () {
  var main = document.getElementById('main'), seen = 'ps-geo-dismissed', got = 'ps-geo';
  if (!main || !window.fetch) return;
  try { if (localStorage.getItem(seen) === '1') return; } catch (e) {}
  var show = function () {
    var box = document.createElement('div'), p = document.createElement('p'), b = document.createElement('button');
    box.className = 'geo-banner'; box.setAttribute('role', 'note');
    p.textContent = 'This game is not available in your country yet';
    b.type = 'button'; b.textContent = '×'; b.setAttribute('aria-label', 'Dismiss');
    b.addEventListener('click', function () { box.parentNode.removeChild(box); try { localStorage.setItem(seen, '1'); } catch (e) {} });
    box.appendChild(p); box.appendChild(b);
    main.parentNode.insertBefore(box, main);
  };
  var cached = null;
  try { cached = sessionStorage.getItem(got); } catch (e) {}
  if (cached !== null) { if (cached === 'VN') show(); return; }
  fetch('/geo.json', { cache: 'no-store', credentials: 'omit' })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
    .then(function (d) {
      var vn = d.vn === true;
      try { sessionStorage.setItem(got, vn ? 'VN' : '-'); } catch (e) {}
      if (vn) show();
    })
    .catch(function () {});
})();
