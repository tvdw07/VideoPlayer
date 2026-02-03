(() => {
  // Nur laufen lassen, wenn das Element existiert
  const el = document.getElementById("player");
  if (!el) return;

  // Video.js Player initialisieren
  const player = videojs(el);
  player.autoplay(true);

  // next URL aus data-Attribut holen
  const nextUrl = el.dataset.nextUrl || null;

  // Keyboard handler nur einmal binden (wichtig bei Turbo/Hot reload)
  if (!window.__vpKeyboardBound) {
    window.__vpKeyboardBound = true;

    document.addEventListener("keydown", (e) => {
      // nicht eingreifen, wenn Nutzer tippt
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;

      // Wenn kein Player verfügbar ist, abbrechen
      // (z.B. wenn man auf einer anderen Seite ist)
      const p = window.videojs?.getPlayer?.("player");
      if (!p) return;

      switch (e.key) {
        case "ArrowRight":
          p.currentTime(p.currentTime() + 10);
          break;

        case "ArrowLeft":
          p.currentTime(Math.max(0, p.currentTime() - 10));
          break;

        case " ":
          e.preventDefault();
          p.paused() ? p.play() : p.pause();
          break;

        default:
          break;
      }
    });
  }

  // Autoplay nächste Episode
  player.on("ended", () => {
    if (nextUrl) {
      window.location.assign(nextUrl);
    }
  });
})();
