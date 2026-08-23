(function () {
  const nav = document.getElementById("nav");
  const toggle = document.querySelector("[data-nav-toggle]");
  const backdrop = document.querySelector("[data-nav-backdrop]");
  const topbar = document.querySelector(".topbar");
  const links = nav ? [...nav.querySelectorAll("a")] : [];

  function setNav(open) {
    if (!nav || !toggle) return;
    nav.classList.toggle("is-open", open);
    toggle.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("nav-open", open);
    if (backdrop) {
      backdrop.classList.toggle("is-open", open);
      backdrop.hidden = !open;
    }
  }

  function closeNav() {
    setNav(false);
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      setNav(!nav.classList.contains("is-open"));
    });
    links.forEach(function (link) {
      link.addEventListener("click", closeNav);
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", closeNav);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeNav();
  });

  window.addEventListener(
    "resize",
    function () {
      if (window.innerWidth > 860) closeNav();
    },
    { passive: true }
  );

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
    if (topbar) topbar.classList.toggle("is-scrolled", window.scrollY > 8);
  }

  window.addEventListener("scroll", setActive, { passive: true });
  setActive();

  document.querySelectorAll("[data-compare]").forEach(function (root) {
    const range = root.querySelector("input");
    const before = root.querySelector(".ba__before");
    if (!range) return;

    function syncWidth() {
      if (before) before.style.width = root.clientWidth + "px";
    }

    function setPos(value) {
      const next = Math.max(8, Math.min(92, Number(value)));
      root.style.setProperty("--pos", next + "%");
      range.value = String(next);
    }

    range.addEventListener("input", function () {
      setPos(range.value);
    });
    syncWidth();
    window.addEventListener("resize", syncWidth, { passive: true });
  });

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
