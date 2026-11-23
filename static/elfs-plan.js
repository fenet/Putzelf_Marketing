(() => {
  const iconFor = (label) => {
    const s = (label || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\u00df/g, 'ss').replace(/\s+/g, ' ').trim();
    if (/delete|remove|trash|loschen|entfernen/.test(s)) return 'bi-trash3';
    if (/search|suchen|filter/.test(s)) return 'bi-search';
    if (/add|create|new|hinzufugen|erstellen|neu/.test(s)) return /employee|mitarbeiter/.test(s) ? 'bi-person-plus' : 'bi-plus-lg';
    if (/save|submit|speichern/.test(s)) return 'bi-check2';
    if (/edit|change|bearbeiten|andern/.test(s)) return 'bi-pencil';
    if (/assign|zuweisen/.test(s)) return 'bi-person-check';
    if (/download|export|herunterladen/.test(s)) return 'bi-download';
    if (/upload|publish|hochladen|veroffentlichen/.test(s)) return 'bi-cloud-arrow-up';
    if (/duplicate|copy|duplizieren|kopieren/.test(s)) return 'bi-copy';
    if (/release|freigeben/.test(s)) return 'bi-unlock';
    if (/inspection|inspect|kontroll|prufen/.test(s)) return 'bi-clipboard2-check';
    if (/schedule|shift|einsatz|plan/.test(s)) return 'bi-calendar3';
    if (/employee|mitarbeiter/.test(s)) return 'bi-people';
    if (/site|client|standort|kunde/.test(s)) return 'bi-building';
    if (/clock in|einstempeln/.test(s)) return 'bi-play-circle';
    if (/clock out|ausstempeln/.test(s)) return 'bi-stop-circle';
    if (/photo|camera|foto/.test(s)) return 'bi-camera';
    if (/tour|route/.test(s)) return 'bi-signpost-2';
    if (/clear|reset|leeren|zurucksetzen/.test(s)) return 'bi-eraser';
    if (/login|sign in|anmelden/.test(s)) return 'bi-box-arrow-in-right';
    if (/logout|sign out|abmelden/.test(s)) return 'bi-box-arrow-right';
    if (/cancel|close|abbrechen|schliessen/.test(s)) return 'bi-x-lg';
    if (/back|zuruck/.test(s)) return 'bi-arrow-left';
    if (/next|continue|weiter/.test(s)) return 'bi-arrow-right';
    if (/report|bericht/.test(s)) return 'bi-file-earmark-bar-graph';
    if (/qr/.test(s)) return 'bi-qr-code';
    if (/document|file|dokument/.test(s)) return 'bi-file-earmark-text';
    if (/view|open|anzeigen|offnen/.test(s)) return 'bi-arrow-up-right';
    return 'bi-arrow-right';
  };
  const decorate = (root = document) => {
    root.querySelectorAll('button, a.btn').forEach((el) => {
      if (el.dataset.epIconDone || el.querySelector('.bi, .ep-icon') || el.type === 'checkbox' || el.type === 'radio') return;
      const visibleText = el.textContent || '';
      if (visibleText.trim() === 'x' || visibleText.trim() === '+' || visibleText.trim() === '-' || visibleText.trim() === '\u00d7') return;
      const label = el.getAttribute('aria-label') || el.getAttribute('title') || visibleText;
      if (!label || !label.trim()) return;
      const icon = document.createElement('i');
      icon.className = `bi ${iconFor(label)} ep-icon`;
      icon.setAttribute('aria-hidden', 'true');
      el.prepend(icon);
      el.dataset.epIconDone = '1';
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => decorate());
  else decorate();
  new MutationObserver((records) => records.forEach((record) => record.addedNodes.forEach((node) => {
    if (node.nodeType === 1) decorate(node.matches?.('button, a.btn') ? node.parentElement || document : node);
  }))).observe(document.documentElement, { childList: true, subtree: true });
})();
