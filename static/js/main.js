// Kararsızım - Ortak JavaScript

document.addEventListener('DOMContentLoaded', () => {
  // Toast bildirimlerini otomatik kapatma
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach(toast => {
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      setTimeout(() => {
        toast.remove();
      }, 300);
    }, 4000);
  });
});
