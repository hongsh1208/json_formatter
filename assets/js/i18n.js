/**
 * 언어 선택 드롭다운(국기 아이콘) 동작.
 * - 실제 언어별 URL 이동은 각 링크의 href(정적으로 생성됨)가 담당하고,
 *   이 스크립트는 드롭다운 열기/닫기와 "직접 선택한 언어"를 localStorage에
 *   기억해 다음 방문부터 그 언어를 우선하도록 하는 역할만 한다.
 * - 브라우저 언어 자동 감지/리다이렉트 로직은 각 페이지 <head>의 인라인
 *   스크립트(scripts/build_site.py의 lang_detect_script)가 담당한다.
 */
(function () {
  "use strict";

  var LANG_KEY = "formix-lang";

  function initLangSwitch() {
    var root = document.querySelector("[data-lang-switch]");
    if (!root) return;
    var toggle = root.querySelector("[data-lang-toggle]");
    var menu = root.querySelector("[data-lang-menu]");
    if (!toggle || !menu) return;

    function closeMenu() {
      menu.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    }
    function openMenu() {
      menu.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
    }

    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      if (menu.hidden) openMenu();
      else closeMenu();
    });

    menu.querySelectorAll("[data-lang-option]").forEach(function (a) {
      a.addEventListener("click", function () {
        try {
          localStorage.setItem(LANG_KEY, a.getAttribute("data-lang-option"));
        } catch (e) {
          /* 저장소를 쓸 수 없는 환경은 조용히 무시 (링크 이동 자체는 정상 동작) */
        }
        // 페이지 이동(href)은 기본 동작 그대로 진행됨.
      });
    });

    document.addEventListener("click", function (e) {
      if (!root.contains(e.target)) closeMenu();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });
  }

  document.addEventListener("DOMContentLoaded", initLangSwitch);
})();
