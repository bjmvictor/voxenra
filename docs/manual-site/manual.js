const search = document.querySelector('#manual-search, #landing-search');
const toggle = document.querySelector('.menu-toggle');
const sidebar = document.querySelector('#sidebar');
if (search) {
  search.addEventListener('input', () => {
    const query = search.value.trim().toLocaleLowerCase();
    let visible = 0;
    document.querySelectorAll('.nav-group, .home-group').forEach(group => {
      let groupVisible = 0;
      group.querySelectorAll('a[data-search]').forEach(link => {
        const match = !query || link.dataset.search.includes(query);
        link.hidden = !match;
        if (match) { visible++; groupVisible++; }
      });
      group.hidden = groupVisible === 0;
    });
    document.querySelector('.no-results').hidden = visible !== 0;
  });
}
if (toggle && sidebar) {
  toggle.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(open));
    if (open) search?.focus();
  });
  sidebar.addEventListener('click', event => {
    if (event.target.closest('a')) {
      sidebar.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      sidebar.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
}
