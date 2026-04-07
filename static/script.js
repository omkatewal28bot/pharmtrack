// Search filter
const si = document.getElementById('search');
if (si) {
  si.addEventListener('input', () => {
    const q = si.value.toLowerCase();
    document.querySelectorAll('tbody tr').forEach(r => {
      r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}

// Delete confirm
function confirmDel(form) {
  if (confirm('Delete this medicine? This cannot be undone.')) form.submit();
}

// Auto dismiss flash
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  }, 3500);
});

// Count-up animation
document.querySelectorAll('.val').forEach(el => {
  const target = parseInt(el.textContent);
  if (isNaN(target)) return;
  let n = 0;
  const step = Math.max(1, Math.floor(target / 30));
  const t = setInterval(() => {
    n = Math.min(n + step, target);
    el.textContent = n;
    if (n >= target) clearInterval(t);
  }, 30);
});