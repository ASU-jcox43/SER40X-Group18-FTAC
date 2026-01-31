// Show a specific page and hide the others
function showPanel(panelId) {
  // Hide all pages
  const pages = document.querySelectorAll('.page');
  pages.forEach(page => page.classList.remove('active'));

  // Show the selected page (if it exists)
  const selected = document.getElementById(panelId + 'Page');
  if (selected) {
    selected.classList.add('active');
  }
}

// Toggle entire right panel
function toggleDetailsPanel() {
  const panel = document.getElementById('detailsPanel');
  panel.classList.toggle('collapsed');
}

// Toggle individual detail sections
function toggleSection(button) {
  const section = button.closest('.detail-section');
  section.classList.toggle('open');
}

// Attach click handlers to header links using a data attribute
document.querySelectorAll('.header-nav a').forEach(link => {
  link.addEventListener('click', e => {

    // Let external links behave normally
    if (link.hasAttribute('data-external')) {
      return;
    }

    e.preventDefault();
    
    const target = link.dataset.target; // read data-target
    if (target) {
      showPanel(target);
    }
  });
});
