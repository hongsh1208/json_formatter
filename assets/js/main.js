/**
 * 공통 스크립트: 다크/라이트 테마 토글, 모바일 네비게이션, 활성 메뉴 표시
 * 모든 페이지에서 </body> 직전에 로드합니다.
 * (초기 테마 적용은 FOUC 방지를 위해 각 페이지 <head>의 인라인 스크립트가 담당합니다.)
 */
(function () {
  "use strict";

  var THEME_KEY = "formix-theme";

  var THEME_LABELS = {
    en: { dark: "Switch to dark mode", light: "Switch to light mode" },
    ko: { dark: "다크 모드로 전환", light: "라이트 모드로 전환" },
    ja: { dark: "ダークモードに切り替え", light: "ライトモードに切り替え" },
    zh: { dark: "切换到深色模式", light: "切换到浅色模式" },
  };

  function currentLangCode() {
    var l = (document.documentElement.getAttribute("lang") || "en").slice(0, 2).toLowerCase();
    return THEME_LABELS[l] ? l : "en";
  }

  function getStoredTheme() {
    try {
      return localStorage.getItem(THEME_KEY);
    } catch (e) {
      return null;
    }
  }

  function setStoredTheme(theme) {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch (e) {
      /* 저장소를 쓸 수 없는 환경(프라이빗 모드 등)은 조용히 무시 */
    }
  }

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var toggle = document.querySelector("[data-theme-toggle]");
    if (toggle) {
      var isDark = theme === "dark";
      var labels = THEME_LABELS[currentLangCode()];
      toggle.setAttribute("aria-pressed", String(isDark));
      toggle.setAttribute("aria-label", isDark ? labels.light : labels.dark);
      toggle.textContent = isDark ? "☀️" : "🌙";
    }
  }

  function initThemeToggle() {
    applyTheme(currentTheme());
    var toggle = document.querySelector("[data-theme-toggle]");
    if (!toggle) return;
    toggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      setStoredTheme(next);
      applyTheme(next);
    });
  }

  function initMobileNav() {
    var navToggle = document.querySelector("[data-nav-toggle]");
    var navLinks = document.querySelector("[data-nav-links]");
    if (!navToggle || !navLinks) return;
    navToggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    navLinks.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        navLinks.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  function initNavDropdowns() {
    // 헤더의 "도구"/"게임" 드롭다운 모두 같은 data-nav-dropdown* 속성을 쓰므로
    // 여기서 한 번에 찾아 각각 독립적으로 열고 닫는 동작을 걸어준다.
    var roots = document.querySelectorAll("[data-nav-dropdown]");
    roots.forEach(function (root) {
      var toggle = root.querySelector("[data-nav-dropdown-toggle]");
      var menu = root.querySelector("[data-nav-dropdown-menu]");
      if (!toggle || !menu) return;

      var hoverCloseTimer = null;

      function closeMenu() {
        clearTimeout(hoverCloseTimer);
        menu.hidden = true;
        toggle.setAttribute("aria-expanded", "false");
      }
      function openMenu() {
        clearTimeout(hoverCloseTimer);
        menu.hidden = false;
        toggle.setAttribute("aria-expanded", "true");
      }
      function scheduleClose() {
        clearTimeout(hoverCloseTimer);
        hoverCloseTimer = setTimeout(closeMenu, 250);
      }

      toggle.addEventListener("click", function (e) {
        e.stopPropagation();
        if (menu.hidden) openMenu();
        else closeMenu();
      });

      // 실제 마우스(hover)가 있는 기기에서는 클릭 없이 올리기만 해도 바로 열리고,
      // 영역을 벗어나면 약간의 지연 후 닫히도록 한다(버튼→메뉴 사이의 작은 간격을
      // 지나갈 때 실수로 닫히지 않게 하기 위함). 터치 기기는 클릭 토글만 사용된다.
      var supportsHover = !window.matchMedia || window.matchMedia("(hover: hover) and (pointer: fine)").matches;
      if (supportsHover) {
        root.addEventListener("mouseenter", openMenu);
        root.addEventListener("mouseleave", scheduleClose);
      }

      document.addEventListener("click", function (e) {
        if (!root.contains(e.target)) closeMenu();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") closeMenu();
      });
    });
  }

  function markActiveNavLink() {
    var path = window.location.pathname.replace(/\/index\.html$/, "/");
    document.querySelectorAll("[data-nav-links] a").forEach(function (a) {
      var linkPath = a.getAttribute("href");
      if (!linkPath) return;
      var normalized = linkPath.replace(/\/index\.html$/, "/");
      if (normalized === path || (normalized !== "/" && path.endsWith(normalized))) {
        a.setAttribute("aria-current", "page");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initThemeToggle();
    initMobileNav();
    initNavDropdowns();
    markActiveNavLink();
  });
})();
