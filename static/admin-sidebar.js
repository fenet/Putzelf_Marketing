(() => {
  const body = document.body;
  const sidebar = document.querySelector('.ep-admin-sidebar');
  const mobileToggle = document.querySelector('.ep-sidebar-mobile-toggle');
  const scrim = document.querySelector('.ep-sidebar-scrim');
  const desktop = window.matchMedia('(min-width: 851px)');
  const setCollapsed = (value) => body.classList.toggle('ep-sidebar-collapsed', value);
  const syncSidebar = () => setCollapsed(desktop.matches && !sidebar?.matches(':hover'));
  syncSidebar();
  sidebar?.addEventListener('mouseenter', () => { if (desktop.matches) setCollapsed(false); });
  sidebar?.addEventListener('mouseleave', () => { if (desktop.matches) setCollapsed(true); });
  desktop.addEventListener?.('change', syncSidebar);
  const setMobileOpen = (open) => {
    body.classList.toggle('ep-mobile-nav-open', open);
    mobileToggle?.setAttribute('aria-expanded', String(open));
  };
  mobileToggle?.addEventListener('click', () => setMobileOpen(!body.classList.contains('ep-mobile-nav-open')));
  scrim?.addEventListener('click', () => setMobileOpen(false));
  sidebar?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setMobileOpen(false)));
})();
