export let browseTabsHash = ['#browse', '#search', '#help', '#vault'];

export function removeHash() {
  history.replaceState('', document.title, window.location.pathname + window.location.search);
}

export function showTab(hash) {
  $('.navbar-nav.swh-browse-nav a[href="' + hash + '"]').tab('show');
  window.scrollTo(0, 0);
}

export function showRequestedTab() {
  let hash = window.location.hash;
  if (hash && browseTabsHash.indexOf(hash) === -1) {
    return;
  }
  if (hash) {
    showTab(hash);
  } else {
    showTab('#browse');
  }
}

export function initMainNavigation() {

  $(document).ready(() => {

    $('.dropdown-submenu a.dropdown-link').on('click', e => {
      $(e.target).next('ul').toggle();
      e.stopPropagation();
      e.preventDefault();
    });

    // Change hash for page reload
    $('.navbar-nav.swh-browse-nav a').on('shown.bs.tab', e => {
      if (e.target.hash.trim() !== '#browse') {
        window.location.hash = e.target.hash;
      } else {
        let hash = window.location.hash;
        if (browseTabsHash.indexOf(hash) !== -1) {
          removeHash();
        }
      }
      showRequestedTab();
    });

    // update displayed tab when the url fragment changes
    $(window).on('hashchange', () => {
      showRequestedTab();
    });

    // show requested tab when loading the page
    showRequestedTab();
  });

}