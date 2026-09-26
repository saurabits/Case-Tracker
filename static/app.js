const modal = document.querySelector('#fileModal');
const frame = document.querySelector('#fileFrame');
const title = document.querySelector('#modalTitle');

document.querySelectorAll('.case-row').forEach((row) => {
  const open = () => { window.location.href = row.dataset.href; };
  row.addEventListener('click', (event) => {
    if (!event.target.closest('button')) open();
  });
  row.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); }
  });
});

document.querySelectorAll('[data-url]').forEach((button) => {
  button.addEventListener('click', () => {
    title.textContent = button.dataset.title;
    frame.src = button.dataset.url;
    modal.showModal();
  });
});

document.querySelector('#closeModal')?.addEventListener('click', () => modal.close());
modal?.addEventListener('click', (event) => { if (event.target === modal) modal.close(); });
modal?.addEventListener('close', () => { frame.src = ''; });
