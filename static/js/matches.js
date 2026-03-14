(function () {
  const list = document.getElementById('matchesList');
  const empty = document.getElementById('emptyMatches');
  const likedList = document.getElementById('likedList');
  const emptyLiked = document.getElementById('emptyLiked');
  const panelMatches = document.getElementById('panelMatches');
  const panelLiked = document.getElementById('panelLiked');
  const tabs = document.querySelectorAll('.matches-tab');

  function escapeHtml(s) {
    if (s == null) return '';
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function defaultAvatarUrl(gender) {
    var g = (gender === 'male' || gender === 'female') ? gender : 'other';
    return '/static/images/avatar-default-' + g + '.svg';
  }

  function formatMatchDate(createdAt) {
    if (!createdAt) return '';
    try {
      var d = new Date(createdAt);
      var now = new Date();
      var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      var yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 1);
      var dDate = new Date(d.getFullYear(), d.getMonth(), d.getDate());
      if (dDate.getTime() === today.getTime()) return 'Сегодня, ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
      if (dDate.getTime() === yesterday.getTime()) return 'Вчера, ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
      return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch (e) { return ''; }
  }

  function renderItem(p, matchId, superLikeByMe, superLikeByThem, createdAt) {
    const name = p.name || 'Профиль';
    const meta = [p.age ? p.age + ' лет' : '', p.city].filter(Boolean).join(' · ');
    const avatar = p.avatar_url
      ? '<img src="' + escapeHtml(p.avatar_url) + '" alt="">'
      : '<img src="' + escapeHtml(defaultAvatarUrl(p.gender)) + '" alt="" class="default-avatar">';
    const superBadge = (superLikeByMe || superLikeByThem) ? ' <span class="match-super-badge" title="Суперлайк">🔥</span>' : '';
    const dateStr = formatMatchDate(createdAt);
    const content =
      '<div class="avatar">' + avatar + '</div>' +
      '<div class="info">' +
      '<div class="name">' + escapeHtml(name) + superBadge + '</div>' +
      (meta ? '<div class="meta">' + escapeHtml(meta) + '</div>' : '') +
      (dateStr ? '<div class="match-date">' + escapeHtml(dateStr) + '</div>' : '') +
      '</div>';
    if (matchId) {
      return '<a class="match-item" href="/chat/' + escapeHtml(matchId) + '">' + content + '</a>';
    }
    return '<div class="match-item match-item-no-link">' + content + '</div>';
  }

  function showMatches(data) {
    const matches = data.matches || [];
    const countEl = document.getElementById('matchesTotalCount');
    const tabMatches = document.querySelector('.matches-tab[data-tab="matches"]');
    if (countEl) countEl.textContent = matches.length ? '(' + matches.length + ')' : '';
    if (tabMatches) {
      const label = tabMatches.querySelector('.tab-label');
      if (label) label.textContent = matches.length ? 'Матчи (' + matches.length + ')' : 'Матчи';
    }
    if (matches.length === 0) {
      list.style.display = 'none';
      empty.style.display = 'block';
    } else {
      empty.style.display = 'none';
      list.style.display = '';
      list.innerHTML = matches.map(function (m) {
        return renderItem(
          m.profile || {},
          m.match_id,
          m.super_like_by_me,
          m.super_like_by_them,
          m.created_at
        );
      }).join('');
    }
  }

  function showLiked(data) {
    const liked = data.liked || [];
    if (liked.length === 0) {
      likedList.style.display = 'none';
      emptyLiked.style.display = 'block';
    } else {
      emptyLiked.style.display = 'none';
      likedList.style.display = '';
      likedList.innerHTML = liked.map(function (item) {
        return renderItem(item.profile || {}, item.match_id, false, false, item.created_at);
      }).join('');
    }
  }

  function loadLiked() {
    fetch('/api/me/liked', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(showLiked)
      .catch(function () {
        likedList.style.display = 'none';
        emptyLiked.style.display = 'block';
      });
  }

  function switchTab(tabName) {
    tabs.forEach(function (t) {
      var isActive = t.dataset.tab === tabName;
      t.classList.toggle('is-active', isActive);
      t.setAttribute('aria-selected', isActive);
    });
    panelMatches.style.display = tabName === 'matches' ? '' : 'none';
    panelLiked.style.display = tabName === 'liked' ? '' : 'none';
    if (tabName === 'liked') loadLiked();
  }

  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      switchTab(t.dataset.tab);
    });
  });

  fetch('/api/matches', { credentials: 'same-origin' })
    .then(function (r) { return r.json(); })
    .then(showMatches)
    .catch(function () {
      list.style.display = 'none';
      empty.style.display = 'block';
    });
})();
