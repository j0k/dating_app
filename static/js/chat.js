(function () {
  const matchId = window.MATCH_ID;
  const header = document.getElementById('chatHeader');
  const messagesEl = document.getElementById('chatMessages');
  const typingEl = document.getElementById('chatTyping');
  const icebreakersEl = document.getElementById('chatIcebreakers');
  const form = document.getElementById('chatForm');
  const input = document.getElementById('messageInput');

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function escapeHtml(s) {
    const div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function messageHtml(m) {
    var read = '';
    if (m.is_mine && m.read_at) read = '<span class="chat-read">Прочитано</span>';
    return '<div class="chat-msg ' + (m.is_mine ? 'mine' : 'theirs') + '" data-id="' + escapeHtml(m.id) + '">' +
      escapeHtml(m.body) + read + '</div>';
  }

  function loadMatch() {
    fetch('/api/matches/' + matchId, { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          header.textContent = 'Чат не найден';
          return;
        }
        const p = data.profile || {};
        header.innerHTML = '<a href="/matches" style="color: inherit; text-decoration: none;">← </a>' + escapeHtml(p.name || 'Чат');
      })
      .catch(() => { header.textContent = 'Ошибка загрузки'; });
  }

  function loadMessages() {
    fetch('/api/matches/' + matchId + '/messages', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => {
        const messages = data.messages || [];
        messagesEl.innerHTML = messages.map(m => messageHtml(m)).join('');
        messagesEl.scrollTop = messagesEl.scrollHeight;
        typingEl.style.display = data.other_typing ? 'block' : 'none';
      })
      .catch(() => {});
  }

  var typingTimer = null;
  function sendTyping() {
    fetch('/api/matches/' + matchId + '/typing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      credentials: 'same-origin',
      body: JSON.stringify({})
    }).catch(() => {});
  }
  function onInputActivity() {
    if (typingTimer) clearTimeout(typingTimer);
    sendTyping();
    typingTimer = setTimeout(function () { typingTimer = null; }, 2000);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const body = input.value.trim();
    if (!body) return;
    input.value = '';
    fetch('/api/matches/' + matchId + '/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      credentials: 'same-origin',
      body: JSON.stringify({ body: body })
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) return;
        const div = document.createElement('div');
        div.className = 'chat-msg mine';
        div.dataset.id = data.id;
        div.innerHTML = escapeHtml(data.body) + '<span class="chat-read">Отправлено</span>';
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
      })
      .catch(() => {});
  });

  input.addEventListener('input', onInputActivity);
  input.addEventListener('keydown', onInputActivity);

  if (icebreakersEl) {
    icebreakersEl.querySelectorAll('.btn-icebreaker').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var text = btn.getAttribute('data-text');
        if (text) input.value = text; input.focus();
      });
    });
  }

  loadMatch();
  loadMessages();
  setInterval(loadMessages, 5000);
})();
