// Anket oluşturma formu: dinamik seçenek ekleme/silme + soru karakter sayacı

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('optionsContainer');
  const addBtn = document.getElementById('addOptionBtn');
  const questionInput = document.getElementById('id_question');
  const counter = document.getElementById('questionCounter');

  const MAX_OPTIONS = 5;
  const MIN_OPTIONS = 2;

  // Karakter sayacı
  if (questionInput && counter) {
    const updateCounter = () => {
      counter.textContent = `${questionInput.value.length} / 150`;
    };
    questionInput.addEventListener('input', updateCounter);
    updateCounter();
  }

  function getRows() {
    return Array.from(container.querySelectorAll('.option-row'));
  }

  function reindex() {
    getRows().forEach((row, i) => {
      const input = row.querySelector('input');
      row.dataset.index = i;
      input.name = `option_${i}`;
      input.placeholder = `Seçenek ${i + 1}`;
    });
    updateRemoveButtons();
    updateAddButton();
  }

  function updateRemoveButtons() {
    const rows = getRows();
    rows.forEach(row => {
      const btn = row.querySelector('.btn-remove-option');
      btn.style.display = rows.length > MIN_OPTIONS ? 'flex' : 'none';
    });
  }

  function updateAddButton() {
    addBtn.style.display = getRows().length >= MAX_OPTIONS ? 'none' : 'inline-flex';
  }

  function addOption() {
    if (getRows().length >= MAX_OPTIONS) return;

    const row = document.createElement('div');
    row.className = 'option-row';
    row.innerHTML = `
      <input type="text" class="form-input option-input" maxlength="80">
      <button type="button" class="btn-remove-option" aria-label="Seçeneği sil">✕</button>
    `;
    container.appendChild(row);

    row.querySelector('.btn-remove-option').addEventListener('click', () => {
      if (getRows().length <= MIN_OPTIONS) return;
      row.remove();
      reindex();
    });

    reindex();
    row.querySelector('input').focus();
  }

  function removeOption(row) {
    if (getRows().length <= MIN_OPTIONS) return;
    row.remove();
    reindex();
  }

  // Mevcut satırların sil butonlarına listener ekle
  container.querySelectorAll('.btn-remove-option').forEach(btn => {
    btn.addEventListener('click', () => removeOption(btn.closest('.option-row')));
  });

  addBtn.addEventListener('click', addOption);

  // İlk durumu güncelle
  updateRemoveButtons();
  updateAddButton();
});
