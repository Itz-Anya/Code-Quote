(function () {
  "use strict";

  var html = document.documentElement;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  var themeButtons = document.querySelectorAll(".theme-switch button");

  function systemTheme() {
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }

  function applyTheme(mode) {
    var resolved = mode === "system" ? systemTheme() : mode;
    html.setAttribute("data-theme", resolved);
    themeButtons.forEach(function (btn) {
      var active = btn.getAttribute("data-mode") === mode;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  themeButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var mode = btn.getAttribute("data-mode");
      localStorage.setItem("cq-theme", mode);
      applyTheme(mode);
    });
  });

  var savedTheme = localStorage.getItem("cq-theme") || "system";
  applyTheme(savedTheme);

  window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", function () {
    if ((localStorage.getItem("cq-theme") || "system") === "system") applyTheme("system");
  });

  var navToggle = document.getElementById("navToggle");
  var mobilePanel = document.getElementById("mobilePanel");
  var mobileCloseBtn = document.getElementById("mobileCloseBtn");

  function setOverlay(open) {
    if (!mobilePanel || !navToggle) return;
    mobilePanel.classList.toggle("open", open);
    mobilePanel.setAttribute("aria-hidden", open ? "false" : "true");
    navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    navToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    navToggle.classList.toggle("is-open", open);
    document.body.classList.toggle("no-scroll", open);
    if (open) {
      var firstLink = mobilePanel.querySelector(".mobile-overlay-links a");
      if (firstLink) firstLink.focus();
    } else {
      navToggle.focus();
    }
  }

  if (navToggle && mobilePanel) {
    navToggle.addEventListener("click", function () {
      setOverlay(!mobilePanel.classList.contains("open"));
    });

    if (mobileCloseBtn) {
      mobileCloseBtn.addEventListener("click", function () { setOverlay(false); });
    }

    mobilePanel.querySelectorAll("[data-close-overlay]").forEach(function (el) {
      el.addEventListener("click", function () { setOverlay(false); });
    });

    mobilePanel.querySelectorAll(".mobile-overlay-links a").forEach(function (link) {
      link.addEventListener("click", function () { setOverlay(false); });
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && mobilePanel.classList.contains("open")) {
        setOverlay(false);
      }
    });
  }

  var quoteImg = document.getElementById("quoteImg");
  var skeleton = document.getElementById("previewSkeleton");
  var previewUrl = document.getElementById("previewUrl");
  var newQuoteBtns = document.querySelectorAll("[data-action='new-quote']");
  var openSvgBtn = document.getElementById("openSvgBtn");
  var themeSelect = document.getElementById("themeSelect");

  var manualCardTheme = null;

  function currentSvgTheme() {
    if (manualCardTheme) return manualCardTheme;
    var mode = localStorage.getItem("cq-theme") || "system";
    return mode === "system" ? systemTheme() : mode;
  }

  function setLoading(isLoading) {
    newQuoteBtns.forEach(function (btn) {
      btn.disabled = isLoading;
    });
    if (skeleton) skeleton.classList.toggle("is-hidden", !isLoading);
    if (quoteImg) quoteImg.classList.toggle("is-visible", !isLoading);
  }

  function loadQuote() {
    if (!quoteImg) return;
    setLoading(true);
    var theme = currentSvgTheme();
    var url = "/api/quote.svg?theme=" + encodeURIComponent(theme) + "&_=" + Date.now();

    var img = new Image();
    img.onload = function () {
      quoteImg.src = img.src;
      if (previewUrl) previewUrl.textContent = "GET /api/quote.svg?theme=" + theme;
      setLoading(false);
    };
    img.onerror = function () {
      setLoading(false);
    };
    img.src = url;
  }

  newQuoteBtns.forEach(function (btn) {
    btn.addEventListener("click", loadQuote);
  });

  if (themeSelect) {
    themeSelect.addEventListener("change", function () {
      manualCardTheme = themeSelect.value;
      loadQuote();
    });
  }

  if (openSvgBtn) {
    openSvgBtn.addEventListener("click", function () {
      window.open(quoteImg.src, "_blank", "noopener");
    });
  }

  function revealInitialQuote() {
    quoteImg.classList.add("is-visible");
    if (skeleton) skeleton.classList.add("is-hidden");
  }

  if (quoteImg) {
    if (quoteImg.complete && quoteImg.naturalWidth > 0) {
      revealInitialQuote();
    } else {
      quoteImg.addEventListener("load", revealInitialQuote);
      quoteImg.addEventListener("error", revealInitialQuote);
    }
  }

  themeButtons.forEach(function (btn) {
    btn.addEventListener("click", loadQuote);
  });

  document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
    var targetId = btn.getAttribute("data-copy-target");
    var target = document.getElementById(targetId);
    if (!target) return;

    var defaultLabel = btn.querySelector(".copy-label");
    var defaultText = defaultLabel ? defaultLabel.textContent : "Copy";

    btn.addEventListener("click", function () {
      var text = target.textContent.trim();

      function onCopied() {
        btn.classList.add("copied");
        if (defaultLabel) defaultLabel.textContent = "Copied";
        showToast("Markdown copied to clipboard");
        setTimeout(function () {
          btn.classList.remove("copied");
          if (defaultLabel) defaultLabel.textContent = defaultText;
        }, 1800);
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(onCopied, function () {
          fallbackCopy(text);
          onCopied();
        });
      } else {
        fallbackCopy(text);
        onCopied();
      }
    });
  });

  function fallbackCopy(text) {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
  }

  var toast = document.getElementById("toast");
  var toastTimer = null;

  function showToast(message) {
    if (!toast) return;
    toast.querySelector(".toast-text").textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toast.classList.remove("show");
    }, 2000);
  }

  var revealEls = document.querySelectorAll(".reveal");

  if ("IntersectionObserver" in window && !reduceMotion.matches) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in-view"); });
  }
})();
