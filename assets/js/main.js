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
      if (window.innerWidth > 1040) closeNav();
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

  document.querySelectorAll("[data-fitment]").forEach(function (root) {
    const car = root.querySelector("[data-fitment-car]");
    const wheel = root.querySelector("[data-fitment-wheel]");
    const note = root.querySelector("[data-fitment-note]");
    const chips = [...root.querySelectorAll(".fitment__chips button")];

    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        chips.forEach(function (other) {
          const on = other === chip;
          other.classList.toggle("is-on", on);
          other.setAttribute("aria-selected", String(on));
        });
        if (car && chip.dataset.car) car.src = chip.dataset.car;
        if (wheel && chip.dataset.wheel) {
          wheel.src = chip.dataset.wheel;
          if (chip.dataset.alt) wheel.alt = chip.dataset.alt;
        }
        if (note && chip.dataset.note) note.textContent = chip.dataset.note;
      });
    });
  });

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

    function posFromPointer(event) {
      const box = root.getBoundingClientRect();
      const x = (event.clientX - box.left) / box.width;
      setPos(Math.round(x * 100));
    }

    root.addEventListener("pointerdown", function (event) {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      posFromPointer(event);
      root.setPointerCapture(event.pointerId);
    });
    root.addEventListener("pointermove", function (event) {
      if (!root.hasPointerCapture(event.pointerId)) return;
      posFromPointer(event);
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
