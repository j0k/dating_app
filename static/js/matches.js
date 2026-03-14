(function () {
  const list = document.getElementById('matchesList');
  const empty = document.getElementById('emptyMatches');

  fetch('/api/matches', { credentials: 'same-origin' })
    .then(r => r.json())
    .then(data => {
      const matches = data.matches || [];
      if (matches.length === 0) {
        list.style.display = 'none';
        empty.style.display = 'block';
        return;
      }
      empty.style.display = 'none';
      list.innerHTML = matches.map(m => {
        const p = m.profile || {};
        const name = p.name || 'Профиль';
        const meta = [p.age ? p.age + ' лет' : '', p.city].filter(Boolean).join(' · ');
        const avatar = p.avatar_url
          ? '<img src="' + escapeHtml(p.avatar_url) + '" alt="">'
          : '👤';
        return '<a class="match-item" href="/chat/' + m.match_id + '">' +
          '<div class="avatar">' + avatar + '</div>' +
          '<div class="info">' +
          '<div class="name">' + escapeHtml(name) + '</div>' +
          (meta ? '<div class="meta">' + escapeHtml(meta) + '</div>' : '') +
          '</div></a>';
      }).join('');
    })
    .catch(() => {
      list.style.display = 'none';
      empty.style.display = 'block';
    });

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }
})();
