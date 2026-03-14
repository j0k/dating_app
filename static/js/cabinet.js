(function () {
  const form = document.getElementById('profileForm');
  const fields = ['name', 'birth_date', 'gender', 'city', 'about', 'interests', 'is_visible'];

  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function loadProfile() {
    fetch('/api/me/profile', { credentials: 'same-origin' })
      .then(r => r.json())
      .then(data => {
        if (data.error) return;
        document.getElementById('name').value = data.name || '';
        document.getElementById('birth_date').value = data.birth_date || '';
        document.getElementById('gender').value = data.gender || '';
        document.getElementById('city').value = data.city || '';
        document.getElementById('about').value = data.about || '';
        document.getElementById('interests').value = (data.interests || []).join(', ');
        document.getElementById('is_visible').checked = data.is_visible !== false;
        document.getElementById('lat').value = data.lat != null ? String(data.lat) : '';
        document.getElementById('lon').value = data.lon != null ? String(data.lon) : '';
        document.getElementById('relationship_goal').value = data.relationship_goal || '';
        document.getElementById('relationship_type').value = data.relationship_type || '';
      })
      .catch(() => {});
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    const latEl = document.getElementById('lat');
    const lonEl = document.getElementById('lon');
    const payload = {
      name: document.getElementById('name').value.trim(),
      birth_date: document.getElementById('birth_date').value || null,
      gender: document.getElementById('gender').value || null,
      city: document.getElementById('city').value.trim() || null,
      about: document.getElementById('about').value.trim() || null,
      interests: document.getElementById('interests').value.trim() || null,
      is_visible: document.getElementById('is_visible').checked,
      lat: latEl && latEl.value ? parseFloat(latEl.value) : null,
      lon: lonEl && lonEl.value ? parseFloat(lonEl.value) : null,
      relationship_goal: document.getElementById('relationship_goal').value || null,
      relationship_type: document.getElementById('relationship_type').value || null
    };
    fetch('/api/me/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
      credentials: 'same-origin',
      body: JSON.stringify(payload)
    })
      .then(r => r.json())
      .then(data => {
        if (data.error || data.errors) {
          alert(data.error || 'Ошибка сохранения');
          return;
        }
        alert('Профиль сохранён');
      })
      .catch(() => alert('Ошибка сети'));
  });

  var profileShareUrl = document.getElementById('profileShareUrl');
  var btnCopyLink = document.getElementById('btnCopyLink');
  var btnShareTg = document.getElementById('btnShareTg');
  if (profileShareUrl && btnShareTg) {
    var shareUrl = profileShareUrl.value;
    btnShareTg.href = 'https://t.me/share/url?url=' + encodeURIComponent(shareUrl) + '&text=' + encodeURIComponent('Мой профиль на Dating App');
  }
  if (btnCopyLink && profileShareUrl) {
    btnCopyLink.addEventListener('click', function () {
      profileShareUrl.select();
      profileShareUrl.setSelectionRange(0, 99999);
      navigator.clipboard.writeText(profileShareUrl.value).then(function () {
        var t = btnCopyLink.textContent;
        btnCopyLink.textContent = 'Скопировано';
        setTimeout(function () { btnCopyLink.textContent = t; }, 2000);
      });
    });
  }

  var inviteLink = document.getElementById('inviteLink');
  var btnCopyInvite = document.getElementById('btnCopyInvite');
  var inviteReferredCount = document.getElementById('inviteReferredCount');
  if (inviteLink) {
    fetch('/api/me/invite', { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.invite_link) inviteLink.value = data.invite_link;
        if (inviteReferredCount) inviteReferredCount.textContent = data.referred_count != null ? data.referred_count : '—';
      })
      .catch(function () { if (inviteLink) inviteLink.placeholder = 'Ошибка загрузки'; });
  }
  if (btnCopyInvite && inviteLink) {
    btnCopyInvite.addEventListener('click', function () {
      inviteLink.select();
      inviteLink.setSelectionRange(0, 99999);
      navigator.clipboard.writeText(inviteLink.value).then(function () {
        var t = btnCopyInvite.textContent;
        btnCopyInvite.textContent = 'Скопировано';
        setTimeout(function () { btnCopyInvite.textContent = t; }, 2000);
      });
    });
  }

  loadProfile();
})();
