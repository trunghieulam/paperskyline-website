(function () {
  var root = document.querySelector('[data-vote-api]');
  if (!root || !window.fetch) return;
  var api = root.getAttribute('data-vote-api'), rows = [].slice.call(root.querySelectorAll('[data-city]'));
  var status = document.querySelector('[data-vote-status]'), counts = {}, widget = null, pending = null;
  var say = function (t) { status.textContent = t; };
  var name = function (li) { return li.getAttribute('data-name'); };
  var seen = function (id) { try { return localStorage.getItem('vote:' + id) === '1'; } catch (e) { return false; } };
  var mark = function (id) { try { localStorage.setItem('vote:' + id, '1'); } catch (e) {} };
  var show = function (li) {
    var id = li.getAttribute('data-city'), n = counts[id] || 0, b = li.querySelector('button');
    li.querySelector('[data-count]').textContent = n === 1 ? '1 vote' : n.toLocaleString('en-GB') + ' votes';
    if (seen(id)) { b.disabled = true; b.textContent = 'Voted'; b.setAttribute('aria-label', 'You voted for ' + name(li)); }
  };
  var rank = function () {
    [].slice.call(root.querySelectorAll('ul')).forEach(function (ul) {
      var lis = [].slice.call(ul.children).map(function (li, i) { return [li, i]; });
      lis.sort(function (a, b) { return (counts[b[0].getAttribute('data-city')] || 0) - (counts[a[0].getAttribute('data-city')] || 0) || a[1] - b[1]; });
      lis.forEach(function (x) { ul.appendChild(x[0]); });
    });
  };
  var send = function (token) {
    var li = pending; pending = null;
    if (!li) return;
    var id = li.getAttribute('data-city');
    fetch(api + '/vote', { method: 'POST', body: JSON.stringify({ city: id, 'cf-turnstile-response': token }), credentials: 'omit', referrerPolicy: 'no-referrer' })
      .then(function (r) {
        if (r.status === 204) { counts[id] = (counts[id] || 0) + 1; mark(id); show(li); say('Thanks. Your vote for ' + name(li) + ' is in.'); }
        else say(r.status === 429 ? 'Too many votes from here for now. Try again later.' : 'That vote did not go through. Try again.');
      })
      .catch(function () { say('That vote did not go through. Check your connection and try again.'); })
      .then(function () { if (widget !== null) window.turnstile.reset(widget); });
  };
  window.psVoteCheck = function () {
    widget = window.turnstile.render(document.querySelector('[data-vote-check]'), {
      sitekey: root.getAttribute('data-vote-key'), action: 'vote', execution: 'execute', appearance: 'interaction-only',
      callback: send, 'error-callback': function () { pending = null; say('The check before voting failed. Try again.'); }
    });
  };
  rows.forEach(function (li) {
    var b = li.querySelector('button');
    b.hidden = false;
    b.addEventListener('click', function () {
      if (widget === null) { say('The check before voting has not loaded yet. Try again in a moment.'); return; }
      pending = li; say('Checking before your vote for ' + name(li) + '...');
      window.turnstile.execute(widget);
    });
    show(li);
  });
  var ids = rows.map(function (li) { return li.getAttribute('data-city'); });
  for (var i = 0; i < ids.length; i += 60) {
    fetch(api + '/votes?cities=' + ids.slice(i, i + 60).join(','), { credentials: 'omit', referrerPolicy: 'no-referrer' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (d) { for (var k in d) counts[k] = Number(d[k]) || 0; rows.forEach(show); rank(); })
      .catch(function () {});
  }
})();
