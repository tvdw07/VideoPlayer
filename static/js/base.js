document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.alert').forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 400);
            }, 3000);
        });
    });

document.addEventListener("submit", (e) => {
  const form = e.target;
  if (form && form.matches("form[data-confirm]")) {
    const msg = form.getAttribute("data-confirm") || "Bist du sicher?";
    if (!window.confirm(msg)) e.preventDefault();
  }
});
