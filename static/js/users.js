(() => {
  const input = document.getElementById("userFilter");
  const rows = [...document.querySelectorAll("#usersTable tbody tr")];
  if (!input) return;

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    rows.forEach(r => {
      const u = r.getAttribute("data-username") || "";
      r.style.display = (!q || u.includes(q)) ? "" : "none";
    });
  });
})();