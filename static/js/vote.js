// Kararsızım - Canlı Oy Verme ve Sonuç Güncelleme

document.addEventListener('DOMContentLoaded', () => {
  const card = document.getElementById('pollDetailCard');
  if (!card) return;

  const voteUrl = card.dataset.voteUrl;
  const optionsList = document.getElementById('optionsList');
  const optionButtons = Array.from(optionsList.querySelectorAll('.vote-option'));
  const showResultsBtn = document.getElementById('showResultsBtn');
  const voteSummary = document.getElementById('voteSummary');
  const totalVotesCount = document.getElementById('totalVotesCount');

  let isSubmitting = false;

  function getCsrfToken() {
    const cookieMatch = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    if (cookieMatch) {
      return decodeURIComponent(cookieMatch[1]);
    }
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  function showToast(message, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');

    const icon = document.createElement('span');
    icon.className = 'toast-icon';
    icon.textContent = type === 'success' ? '✓' : '✕';

    const text = document.createElement('span');
    text.className = 'toast-text';
    text.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.type = 'button';
    closeBtn.className = 'toast-close';
    closeBtn.setAttribute('aria-label', 'Kapat');
    closeBtn.textContent = '×';
    closeBtn.addEventListener('click', () => toast.remove());

    toast.appendChild(icon);
    toast.appendChild(text);
    toast.appendChild(closeBtn);
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  function setButtonsDisabled(disabled) {
    optionButtons.forEach(btn => {
      btn.disabled = disabled;
    });
  }

  function renderResults(data) {
    optionsList.classList.add('show-results');

    const optionMap = new Map();
    data.options.forEach(opt => optionMap.set(opt.id, opt));

    optionButtons.forEach(btn => {
      const optId = parseInt(btn.dataset.optionId, 10);
      const optData = optionMap.get(optId);
      if (!optData) return;

      btn.dataset.percent = optData.percent;
      btn.dataset.votes = optData.votes;

      const progress = btn.querySelector('.vote-progress');
      const percentEl = btn.querySelector('.vote-percent');
      const countEl = btn.querySelector('.vote-count');
      const statsEl = btn.querySelector('.vote-stats');
      const checkEl = btn.querySelector('.vote-check');

      if (progress) {
        progress.style.width = `${optData.percent}%`;
      }
      if (percentEl) {
        percentEl.textContent = `${optData.percent}%`;
      }
      if (countEl) {
        countEl.textContent = `(${optData.votes})`;
      }
      if (statsEl) {
        statsEl.hidden = false;
      }

      const isSelected = data.my_option_id === optId;
      btn.classList.toggle('is-selected', isSelected);
      if (checkEl) {
        checkEl.hidden = !isSelected;
      }
    });

    if (totalVotesCount) {
      totalVotesCount.textContent = data.total;
    }
    if (voteSummary) {
      voteSummary.hidden = false;
    }
    if (showResultsBtn) {
      showResultsBtn.hidden = true;
    }
  }

  async function submitVote(optionId) {
    if (isSubmitting) return;
    isSubmitting = true;
    setButtonsDisabled(true);

    try {
      const response = await fetch(voteUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify({ option_id: optionId }),
      });

      const data = await response.json();

      if (!response.ok || !data.ok) {
        showToast(data.error || 'Bir şeyler ters gitti, tekrar dener misin?', 'error');
        return;
      }

      renderResults(data);
      showToast('Oyun kaydedildi ✓', 'success');
    } catch (err) {
      showToast('Bağlantı hatası oluştu, tekrar dener misin?', 'error');
    } finally {
      isSubmitting = false;
      setButtonsDisabled(false);
    }
  }

  optionButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const optionId = parseInt(btn.dataset.optionId, 10);
      if (!Number.isNaN(optionId)) {
        submitVote(optionId);
      }
    });
  });

  if (showResultsBtn) {
    showResultsBtn.addEventListener('click', () => {
      optionsList.classList.add('show-results');
      optionButtons.forEach(btn => {
        const progress = btn.querySelector('.vote-progress');
        const statsEl = btn.querySelector('.vote-stats');
        if (progress) {
          progress.style.width = `${btn.dataset.percent || 0}%`;
        }
        if (statsEl) {
          statsEl.hidden = false;
        }
      });
      if (voteSummary) {
        voteSummary.hidden = false;
      }
      showResultsBtn.hidden = true;
    });
  }
});
