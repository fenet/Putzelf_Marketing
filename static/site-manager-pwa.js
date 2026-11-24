(() => {
  const button = document.getElementById("manager-pwa-install");
  const dialog = document.getElementById("manager-pwa-help");
  const title = document.getElementById("manager-pwa-help-title");
  const copy = document.getElementById("manager-pwa-help-copy");
  const close = document.getElementById("manager-pwa-help-close");
  if (!button || !dialog || !copy) return;

  const german = (document.documentElement.lang || "").toLowerCase().startsWith("de");
  const apple = /iphone|ipad|ipod/i.test(navigator.userAgent)
    || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const installed = window.matchMedia("(display-mode: standalone)").matches
    || navigator.standalone === true;
  let installPrompt = null;

  if (german) {
    button.setAttribute("aria-label", "Putzelf Manager installieren");
    button.title = "Putzelf Manager installieren";
    const label = button.querySelector("span");
    if (label) label.textContent = "Installieren";
    if (title) title.textContent = "Putzelf Manager installieren";
    if (close) close.textContent = "Schließen";
  }
  if (installed) button.hidden = true;

  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPrompt = event;
    button.hidden = false;
  });

  window.addEventListener("appinstalled", () => {
    button.hidden = true;
    installPrompt = null;
  });

  button.addEventListener("click", async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const result = await installPrompt.userChoice;
      if (result?.outcome === "accepted") button.hidden = true;
      installPrompt = null;
      return;
    }

    copy.textContent = german
      ? (apple
        ? "Tippen Sie auf „Teilen“ und wählen Sie „Zum Home-Bildschirm“."
        : "Öffnen Sie das Browser-Menü und wählen Sie „App installieren“ oder „Zum Startbildschirm hinzufügen“. ")
      : (apple
        ? "Tap Share, then choose “Add to Home Screen”."
        : "Open your browser menu and choose “Install app” or “Add to Home screen”.");
    dialog.showModal();
  });

  close?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/manager-sw.js", { scope: "/" })
      .catch((error) => console.error("Site manager service worker registration failed", error));
  }
})();
