(() => {
  const form = document.getElementById('user-filter-form');
  if (!form) return;
  const sortField = document.getElementById('sort-field');
  const directionField = document.getElementById('direction-field');

  document.querySelectorAll('.sort-button').forEach((button) => {
    button.addEventListener('click', () => {
      const nextSort = button.dataset.sort;
      directionField.value = sortField.value === nextSort && directionField.value === 'asc' ? 'desc' : 'asc';
      sortField.value = nextSort;
      form.submit();
    });
  });

  document.querySelectorAll('.page-jump').forEach((button) => {
    button.addEventListener('click', () => {
      if (button.closest('.page-item')?.classList.contains('disabled')) return;
      let pageInput = form.querySelector('input[name="page"]');
      if (!pageInput) {
        pageInput = document.createElement('input');
        pageInput.type = 'hidden';
        pageInput.name = 'page';
        form.appendChild(pageInput);
      }
      pageInput.value = button.dataset.page;
      form.submit();
    });
  });

  document.querySelectorAll('form[data-confirm]').forEach((confirmForm) => {
    confirmForm.addEventListener('submit', (event) => {
      if (!window.confirm(confirmForm.dataset.confirm)) event.preventDefault();
    });
  });
})();
