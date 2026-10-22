  // Category navigation (left panel)
  document.querySelectorAll(".left [data-url]").forEach(function (card) {
    card.addEventListener("click", function () {
      if (card.classList.contains("active-category")) {
        return; // already on this page
      }
      window.location.href = card.dataset.url;
    });
  });