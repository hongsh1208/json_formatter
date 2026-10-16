// 방명록(guestbook.html) 인터랙션.
// 언어별로 분리하지 않고 전체 언어 방문자가 같은 메시지 목록을 공유한다
// (타자 속도 테스트 랭킹과 달리 lang 파라미터를 보내지 않음).
(function () {
  "use strict";

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var wrap = document.getElementById("gb-form");
    var list = document.getElementById("gb-list");
    var nicknameInput = document.getElementById("gb-nickname");
    var messageInput = document.getElementById("gb-message");
    var submitBtn = document.getElementById("gb-btn-submit");
    var statusEl = document.getElementById("gb-submit-status");
    if (!wrap || !list || !messageInput || !submitBtn) return;

    try {
      var savedNickname = localStorage.getItem("formix-guestbook-nickname");
      if (savedNickname && nicknameInput) nicknameInput.value = savedNickname;
    } catch (e) {
      /* localStorage 접근 불가 시 조용히 무시 */
    }

    function renderList(entries) {
      if (!entries || entries.length === 0) {
        list.innerHTML = '<li class="gb-status">' + escapeHtml(wrap.getAttribute("data-gb-empty") || "") + "</li>";
        return;
      }
      list.innerHTML = entries
        .map(function (e) {
          var when = "";
          try {
            when = new Date(e.created_at).toLocaleString();
          } catch (err) {
            /* 날짜 파싱 실패 시 빈 문자열로 둠 */
          }
          return (
            '<li class="gb-entry">' +
            '<span class="gb-entry-name">' + escapeHtml(e.nickname) + "</span>" +
            '<span class="gb-entry-message">' + escapeHtml(e.message) + "</span>" +
            '<span class="gb-entry-time">' + escapeHtml(when) + "</span>" +
            "</li>"
          );
        })
        .join("");
    }

    function loadList() {
      list.innerHTML = '<li class="gb-status">' + escapeHtml(wrap.getAttribute("data-gb-loading") || "") + "</li>";
      fetch("/api/guestbook?limit=30")
        .then(function (res) {
          if (!res.ok) throw new Error("bad status");
          return res.json();
        })
        .then(function (data) {
          renderList(data.entries);
        })
        .catch(function () {
          list.innerHTML = '<li class="gb-status">' + escapeHtml(wrap.getAttribute("data-gb-error") || "") + "</li>";
        });
    }

    function submitMessage() {
      var nickname = (nicknameInput && nicknameInput.value ? nicknameInput.value : "").trim().slice(0, 20);
      var message = (messageInput.value || "").replace(/[\r\n]+/g, " ").trim().slice(0, 100);
      if (!message) {
        messageInput.focus();
        return;
      }
      try {
        if (nickname) localStorage.setItem("formix-guestbook-nickname", nickname);
      } catch (e) {
        /* 조용히 무시 */
      }
      submitBtn.disabled = true;
      statusEl.className = "gb-submit-status";
      statusEl.textContent = wrap.getAttribute("data-gb-submitting") || "";
      fetch("/api/guestbook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nickname: nickname, message: message }),
      })
        .then(function (res) {
          if (res.status === 429) {
            statusEl.className = "gb-submit-status is-error";
            statusEl.textContent = wrap.getAttribute("data-gb-rate-limited") || "";
            submitBtn.disabled = false;
            return null;
          }
          if (!res.ok) throw new Error("bad status");
          return res.json();
        })
        .then(function (data) {
          if (!data) return;
          if (data.ok) {
            statusEl.className = "gb-submit-status is-success";
            statusEl.textContent = wrap.getAttribute("data-gb-success") || "";
            messageInput.value = "";
            loadList();
          } else {
            statusEl.className = "gb-submit-status is-error";
            statusEl.textContent = wrap.getAttribute("data-gb-error-submit") || "";
          }
          submitBtn.disabled = false;
        })
        .catch(function () {
          statusEl.className = "gb-submit-status is-error";
          statusEl.textContent = wrap.getAttribute("data-gb-error-submit") || "";
          submitBtn.disabled = false;
        });
    }

    submitBtn.addEventListener("click", submitMessage);
    messageInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        submitMessage();
      }
    });

    loadList();
  });
})();
