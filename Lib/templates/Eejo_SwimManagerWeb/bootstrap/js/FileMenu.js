//  //<!-- Defer ensures DOM is ready when script runs -->

//     document.addEventListener('DOMContentLoaded', () => {
//       const qs  = (s, el = document) => el.querySelector(s);
//       const qsa = (s, el = document) => Array.from(el.querySelectorAll(s));

//       const toggleBtn = qs('.nav-toggle');
//       const menu = qs('#main-menu');
//       const fileBtn = qs('#file-btn');
//       const fileMenu = qs('#file-submenu');
//       const fileItems = qsa('[role="menuitem"]', fileMenu);
//       const log = qs('#log');

//       function openFileMenu() {
//         if (fileBtn.getAttribute('aria-expanded') === 'true') return;
//         fileBtn.setAttribute('aria-expanded', 'true');
//         fileMenu.classList.add('open');
//         setTimeout(() => fileItems[0]?.focus(), 0); // focus first item
//       }

//       function closeFileMenu() {
//         if (fileBtn.getAttribute('aria-expanded') === 'false') return;
//         fileBtn.setAttribute('aria-expanded', 'false');
//         fileMenu.classList.remove('open');
//       }

//       function toggleFileMenu() {
//         (fileBtn.getAttribute('aria-expanded') === 'true') ? closeFileMenu() : openFileMenu();
//       }

//       // Mobile hamburger toggle
//       toggleBtn?.addEventListener('click', () => {
//         const expanded = toggleBtn.getAttribute('aria-expanded') === 'true';
//         toggleBtn.setAttribute('aria-expanded', String(!expanded));
//         menu.classList.toggle('open', !expanded);
//         if (!expanded) setTimeout(() => qs('.menubar .menuitem-btn')?.focus(), 0);
//       });

//       // Click to open/close File submenu
//       fileBtn.addEventListener('click', () => { toggleFileMenu(); });

//       // Keyboard on File button
//       fileBtn.addEventListener('keydown', (e) => {
//         const key = e.key;
//         if (key === 'Enter' || key === ' ' || key === 'Spacebar') { e.preventDefault(); toggleFileMenu(); }
//         else if (key === 'ArrowDown') { e.preventDefault(); openFileMenu(); }
//         else if (key === 'Escape') { e.preventDefault(); closeFileMenu(); }
//       });

// // Close submenu (and optionally the mobile menu) after a submenu click
// fileItems.forEach(btn => {
//   btn.addEventListener('click', () => {
//     const action = btn.dataset.action;

//     // your action handling
//     if (action === 'print') window.print();
//     // ... hook other actions here (new, open, save, export, close, etc.)

//     // 1) Always close the File submenu
//     closeFileMenu();

//     // 2) If mobile hamburger is open, collapse it too
//     const isMobile = window.matchMedia('(max-width: 767px)').matches;
//     const mainMenuIsOpen = menu.classList.contains('open');
//     if (isMobile && mainMenuIsOpen) {
//       toggleBtn?.setAttribute('aria-expanded', 'false');
//       menu.classList.remove('open');
//     }
//   });
// });


//       // Keyboard inside submenu (robust: listen on document while menu open)
//       document.addEventListener('keydown', (e) => {
//         if (fileBtn.getAttribute('aria-expanded') !== 'true') return;
//         const items = fileItems;
//         if (!items.length) return;

//         const active = document.activeElement;
//         let i = items.indexOf(active);
//         if (i === -1) i = 0;

//         if (e.key === 'Escape') { e.preventDefault(); closeFileMenu(); fileBtn.focus(); }
//         else if (e.key === 'ArrowDown') { e.preventDefault(); items[(i + 1) % items.length].focus(); }
//         else if (e.key === 'ArrowUp') { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
//         else if (e.key === 'Home') { e.preventDefault(); items[0].focus(); }
//         else if (e.key === 'End') { e.preventDefault(); items[items.length - 1].focus(); }
//       });

//       // Outside click closes submenu (capture + composedPath for reliability)
//       function fallbackPath(node) {
//         const path = [];
//         while (node) { path.push(node); node = node.parentNode; }
//         return path;
//       }
//       document.addEventListener('click', (e) => {
//         const path = e.composedPath ? e.composedPath() : fallbackPath(e.target);
//         const inside = path.includes(fileBtn) || path.includes(fileMenu);
//         if (!inside) closeFileMenu();
//       }, true);

//       // Demo action logging
//       fileItems.forEach(btn => {
//         btn.addEventListener('click', () => {
//           const action = btn.dataset.action;
//           if (log) log.textContent = `Action: ${action}`;
//           if (action === 'print') window.print();
//           if (action === 'close') closeFileMenu();
//         });
//       });

//       // Responsive transition: close submenu when leaving mobile
//       let lastIsMobile = window.matchMedia('(max-width: 767px)').matches;
//       window.addEventListener('resize', () => {
//         const isMobile = window.matchMedia('(max-width: 767px)').matches;
//         if (lastIsMobile && !isMobile) {
//           toggleBtn?.setAttribute('aria-expanded', 'false');
//           menu?.classList.remove('open');
//           closeFileMenu();
//         }
//         lastIsMobile = isMobile;
//       });
//     });
  



    // Attach a toggle behavior to a button and its menu
    function wireMenuToggle(buttonId, menuId) {
      const btn  = document.getElementById(buttonId);
      const menu = document.getElementById(menuId);
      if (!btn || !menu) return;

      // Toggle on button click
      btn.addEventListener('click', (ev) => {
        ev.preventDefault();
        const isOpen = !menu.classList.contains('open');

        // Close any other open top-level menus
        document.querySelectorAll('.dropdown.open').forEach(dd => {
          if (dd !== menu) dd.classList.remove('open');
        });
        document.querySelectorAll('.menu-btn[aria-expanded="true"]').forEach(b => {
          if (b !== btn) b.setAttribute('aria-expanded', 'false');
        });

        menu.classList.toggle('open', isOpen);
        btn.setAttribute('aria-expanded', String(isOpen));

        // Focus first item for accessibility when opened
        if (isOpen) {
          const first = menu.querySelector('a, button, [tabindex]:not([tabindex="-1"])');
          first && first.focus();
        }
      });

      // Close on outside click
      document.addEventListener('click', (ev) => {
        if (!menu.classList.contains('open')) return;
        const isInside = menu.contains(ev.target) || btn.contains(ev.target);
        if (!isInside) {
          menu.classList.remove('open');
          btn.setAttribute('aria-expanded', 'false');
        }
      });

      // Close on ESC
      document.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape' && menu.classList.contains('open')) {
          menu.classList.remove('open');
          btn.setAttribute('aria-expanded', 'false');
          btn.focus();
        }
      });
    }

    // Wire both top-level menus
    document.addEventListener('DOMContentLoaded', () => {
      wireMenuToggle('File-btn', 'File-menu');
      wireMenuToggle('Report-btn', 'Report-menu');
    });
  