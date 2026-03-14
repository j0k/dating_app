/**
 * Подставляет в шапку три показателя: Зарегистрировано, Реальных, Онлайн.
 * Если в шапке только «В сети: N» — на сервере отдаётся старый base.html, нужен деплой.
 */
(function () {
  var el = document.querySelector('.header-stats');
  if (!el) return;
  fetch('/api/stats', { credentials: 'same-origin' })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      el.innerHTML = 'Зарегистрировано: <strong>' + (d.total != null ? d.total : 0) + '</strong> · Реальных: <strong>' + (d.real != null ? d.real : 0) + '</strong> · Онлайн: <strong>' + (d.online != null ? d.online : 0) + '</strong>';
    })
    .catch(function () {});
})();
