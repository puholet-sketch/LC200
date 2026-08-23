(function () {
  const nav = document.getElementById("nav");
  const toggle = document.querySelector("[data-nav-toggle]");
  const links = nav ? [...nav.querySelectorAll("a")] : [];

  function closeNav() {
    if (!nav || !toggle) return;
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      const open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    links.forEach(function (link) {
      link.addEventListener("click", closeNav);
    });
  }

  const sections = links
    .map(function (link) {
      const id = link.getAttribute("href");
      return id && id.startsWith("#") ? document.querySelector(id) : null;
    })
    .filter(Boolean);

  function setActive() {
    const y = window.scrollY + 96;
    let current = null;
    sections.forEach(function (section) {
      if (section.offsetTop <= y) current = section;
    });
    links.forEach(function (link) {
      const match = current && link.getAttribute("href") === "#" + current.id;
      link.classList.toggle("is-active", Boolean(match));
    });
  }

  window.addEventListener("scroll", setActive, { passive: true });
  setActive();

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduce && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) entry.target.classList.add("is-in");
        });
      },
      { threshold: 0.12 }
    );
    document.querySelectorAll(".reveal").forEach(function (el) {
      io.observe(el);
    });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) {
      el.classList.add("is-in");
    });
  }
})();
