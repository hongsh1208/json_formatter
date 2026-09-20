/**
 * 공통 스크립트: 다크/라이트 테마 토글, 모바일 네비게이션, 활성 메뉴 표시
 * 모든 페이지에서 </body> 직전에 로드합니다.
 * (초기 테마 적용은 FOUC 방지를 위해 각 페이지 <head>의 인라인 스크립트가 담당합니다.)
 */
(function () {
  "use strict";

  var THEME_KEY = "wtb-theme";

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
      toggle.setAttribute("aria-pressed", String(isDark));
      toggle.setAttribute("aria-label", isDark ? "라이트 모드로 전환" : "다크 모드로 전환");
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
    markActiveNavLink();
  });
})();
