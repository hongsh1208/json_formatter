/**
 * EEA / 영국 / 스위스 방문자를 위한 쿠키·광고 동의 배너
 * - 서버가 없는 정적 사이트이므로 IP 기반 지역 판별 대신 브라우저 타임존을
 *   이용한 best-effort 추정을 사용한다 (완벽하지 않지만 실용적인 근사치).
 * - 선택 결과는 localStorage에 저장되고, 저장된 값이 없을 때만 배너를 띄운다.
 * - 지금은 사이트에 광고 스크립트가 없으므로 이 배너는 "동의를 수집해 저장하는
 *   틀"의 역할만 한다. 추후 Google AdSense(Funding Choices 등 공식 CMP)를
 *   붙일 때 window.formixConsent.get() 값을 읽어 광고 스크립트 로드 여부를
 *   결정하면 된다.
 * - 푸터의 "쿠키 설정" 버튼으로 언제든 다시 열어 선택을 바꿀 수 있다.
 */
(function () {
  "use strict";

  var STORAGE_KEY = "formix-consent"; // "accepted" | "rejected"

  var LANG = (function () {
    var l = (document.documentElement.getAttribute("lang") || "en").slice(0, 2).toLowerCase();
    return { en: 1, ko: 1, ja: 1, zh: 1 }[l] ? l : "en";
  })();

  var MESSAGES = {
    en: {
      text: 'We use cookies for essential site functionality and, if introduced later, for advertising and analytics. If you are visiting from the EEA, UK, or Switzerland, please choose your preference below. See our <a href="/privacy.html">Privacy Policy</a> for details.',
      acceptAll: "Accept all",
      rejectNonEssential: "Reject non-essential",
      settingsLabel: "Cookie preferences",
      savedAccepted: "You've accepted cookies for advertising/analytics.",
      savedRejected: "You've rejected non-essential cookies.",
      close: "Close",
    },
    ko: {
      text: 'Formix는 필수 사이트 기능과, 추후 도입 시 광고·분석을 위해 쿠키를 사용할 수 있습니다. EEA·영국·스위스에서 접속하셨다면 아래에서 선택해주세요. 자세한 내용은 <a href="/privacy.html">개인정보처리방침</a>을 참고해주세요.',
      acceptAll: "모두 동의",
      rejectNonEssential: "필수 외 거부",
      settingsLabel: "쿠키 설정",
      savedAccepted: "광고·분석 쿠키에 동의하셨습니다.",
      savedRejected: "필수 외 쿠키를 거부하셨습니다.",
      close: "닫기",
    },
    ja: {
      text: 'Formixは必須のサイト機能、また今後導入する場合は広告・分析のためにCookieを使用することがあります。EEA・英国・スイスからアクセスされている場合は、以下からご選択ください。詳しくは<a href="/privacy.html">プライバシーポリシー</a>をご覧ください。',
      acceptAll: "すべて同意",
      rejectNonEssential: "必須以外を拒否",
      settingsLabel: "Cookie設定",
      savedAccepted: "広告・分析Cookieに同意しました。",
      savedRejected: "必須以外のCookieを拒否しました。",
      close: "閉じる",
    },
    zh: {
      text: 'Formix会使用 Cookie 以实现必要的网站功能，如后续引入广告或分析功能也会用到。如果您从 EEA、英国或瑞士访问，请在下方进行选择。详情请参阅<a href="/privacy.html">隐私政策</a>。',
      acceptAll: "全部同意",
      rejectNonEssential: "拒绝非必要",
      settingsLabel: "Cookie 设置",
      savedAccepted: "您已同意用于广告/分析的 Cookie。",
      savedRejected: "您已拒绝非必要 Cookie。",
      close: "关闭",
    },
  };
  var T = MESSAGES[LANG];

  // 유럽 지역(EEA) + 영국 + 스위스에 해당하는 IANA 타임존을 추정한다.
  // 완전한 목록은 아니지만 실제 사용 지역을 폭넓게 커버하는 best-effort 근사치다.
  function isLikelyEeaUkChTimezone() {
    var tz = "";
    try {
      tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    } catch (e) {
      return false;
    }
    if (tz.indexOf("Europe/") === 0) return true;
    var extra = [
      "Atlantic/Canary", "Atlantic/Madeira", "Atlantic/Azores", "Atlantic/Faroe",
      "Africa/Ceuta",
    ];
    return extra.indexOf(tz) !== -1;
  }

  function getStoredConsent() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function setStoredConsent(value) {
    try {
      localStorage.setItem(STORAGE_KEY, value);
    } catch (e) {
      /* 저장소를 쓸 수 없는 환경은 조용히 무시 */
    }
  }

  function buildBanner() {
    var wrap = document.createElement("div");
    wrap.className = "consent-banner";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-live", "polite");
    wrap.setAttribute("aria-label", T.settingsLabel);
    wrap.innerHTML =
      '<div class="consent-banner-inner">' +
      '<p class="consent-banner-text">' + T.text + "</p>" +
      '<div class="consent-banner-actions">' +
      '<button type="button" class="btn btn-sm" data-consent-reject>' + T.rejectNonEssential + "</button>" +
      '<button type="button" class="btn btn-primary btn-sm" data-consent-accept>' + T.acceptAll + "</button>" +
      "</div>" +
      "</div>";
    return wrap;
  }

  function showBanner() {
    if (document.querySelector(".consent-banner")) return;
    var banner = buildBanner();
    document.body.appendChild(banner);
    // 트랜지션이 자연스럽게 보이도록 다음 프레임에 표시 클래스를 추가
    requestAnimationFrame(function () {
      banner.classList.add("is-visible");
    });

    banner.querySelector("[data-consent-accept]").addEventListener("click", function () {
      setStoredConsent("accepted");
      hideBanner(banner);
    });
    banner.querySelector("[data-consent-reject]").addEventListener("click", function () {
      setStoredConsent("rejected");
      hideBanner(banner);
    });
  }

  function hideBanner(banner) {
    banner.classList.remove("is-visible");
    setTimeout(function () {
      if (banner.parentNode) banner.parentNode.removeChild(banner);
    }, 250);
  }

  function initFooterSettingsLink() {
    var link = document.querySelector("[data-cookie-settings]");
    if (!link) return;
    link.addEventListener("click", function (e) {
      e.preventDefault();
      showBanner();
    });
  }

  // 공개 API — 추후 광고 스크립트를 붙일 때 동의 여부를 읽는 용도
  window.formixConsent = {
    get: getStoredConsent,
    open: showBanner,
  };

  document.addEventListener("DOMContentLoaded", function () {
    initFooterSettingsLink();
    var stored = getStoredConsent();
    if (!stored && isLikelyEeaUkChTimezone()) {
      showBanner();
    }
  });
})();
