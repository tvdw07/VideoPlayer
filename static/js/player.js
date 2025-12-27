const player = videojs('player');
player.autoplay(true);

// Tastatursteuerung GLOBAL
document.addEventListener('keydown', (e) => {

  // nicht eingreifen, wenn Nutzer tippt
  if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
    return;
  }

  switch (e.key) {
    case 'ArrowRight':
      player.currentTime(player.currentTime() + 10);
      break;

    case 'ArrowLeft':
      player.currentTime(player.currentTime() - 10);
      break;

    case ' ':
      e.preventDefault();
      player.paused() ? player.play() : player.pause();
      break;
  }
});

// Autoplay nächste Episode
player.on('ended', () => {
  if (NEXT_URL) {
    window.location.href = NEXT_URL;
  }
});
