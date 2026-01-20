function showPanel(panelId) {
  // hide all pages
  const pages = document.querySelectorAll('.page');
  pages.forEach(page => page.classList.remove('active'));

  // show the selected page
  const selected = document.getElementById(panelId + 'Page');
  selected.classList.add('active');
}

// Example: hook header links
document.querySelectorAll('.header-nav a').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const target = link.textContent.toLowerCase().replace(' ', '');
    showPanel(target);
  });
});
