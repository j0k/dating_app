(function () {
  const messagesEl = document.getElementById('mapChatMessages');
  const form = document.getElementById('mapChatForm');
  const textEl = document.getElementById('mapChatText');
  const submitBtn = document.getElementById('mapChatSubmit');
  if (!messagesEl || !form) return;

  function escapeHtml(s) {
    if (s == null) return '';
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function getCsrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function renderMessage(m) {
    var time = '';
    if (m.created_at) {
      try {
        var d = new Date(m.created_at);
        time = d.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
      } catch (e) {}
    }
    return '<div class="map-chat-item">' +
      '<span class="map-chat-item-author">' + escapeHtml(m.author) + '</span>' +
      (time ? ' <span class="map-chat-item-time">' + escapeHtml(time) + '</span>' : '') +
      '<p class="map-chat-item-text">' + escapeHtml(m.text) + '</p></div>';
  }

  function loadMessages() {
    fetch('/api/map-chat', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var list = data.messages || [];
        messagesEl.innerHTML = list.length ? list.map(renderMessage).join('') : '<p class="map-chat-empty">Пока нет сообщений.</p>';
        messagesEl.scrollTop = 0;
      })
      .catch(function () {
        messagesEl.innerHTML = '<p class="map-chat-empty">Не удалось загрузить сообщения.</p>';
      });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var text = (textEl.value || '').trim();
    if (!text) return;
    submitBtn.disabled = true;
    fetch('/api/map-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      credentials: 'same-origin',
      body: JSON.stringify({ text: text }),
    })
      .then(function (r) { return r.json().then(function (data) { return { ok: r.ok, data: data }; }); })
      .then(function (result) {
        submitBtn.disabled = false;
        if (result.ok && result.data.id) {
          textEl.value = '';
          var html = renderMessage({ author: result.data.author, text: text, created_at: result.data.created_at });
          if (messagesEl.querySelector('.map-chat-empty')) messagesEl.innerHTML = '';
          messagesEl.insertAdjacentHTML('afterbegin', html);
          messagesEl.scrollTop = 0;
        } else {
          alert(result.data.error || 'Не удалось отправить');
        }
      })
      .catch(function () {
        submitBtn.disabled = false;
        alert('Не удалось отправить');
      });
  });

  loadMessages();
})();
