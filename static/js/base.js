document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.alert').forEach(alert => {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 400);
            }, 3000);
        });
    });