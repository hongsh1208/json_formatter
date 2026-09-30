/**
 * SQL 포매터 / 정렬기
 * - 오픈소스 sql-formatter 라이브러리(MIT 라이선스, tools/vendor/sql-formatter.min.js)를
 *   이 페이지에서만 로드해서 사용한다. 라이브러리는 window.sqlFormatter로 노출된다.
 * - 이 도구는 SQL을 "정렬(포맷팅)"할 뿐, 쿼리가 실제 데이터베이스에서 의미적으로 올바른지는
 *   검증하지 않는다. 괄호/따옴표가 맞지 않는 등 구문 자체를 해석할 수 없을 때만 오류로 표시한다.
 *
 * 입력값은 서버로 전송되지 않고 이 파일 안에서만(브라우저 내에서) 처리됩니다.
 */
(function () {
  "use strict";

  var LANG = (function () {
    var l = (document.documentElement.getAttribute("lang") || "en").slice(0, 2).toLowerCase();
    return { en: 1, ko: 1, ja: 1, zh: 1 }[l] ? l : "en";
  })();

  var MESSAGES = {
    en: {
      statusIdleText: "Paste a SQL query", statusIdleTop: "Idle",
      statusInvalidText: "Couldn't parse this SQL", statusInvalidTop: "Invalid",
      statusValidText: "Formatted", statusValidTop: "Done",
      detailInvalid: function (line, col) { return "Check around line " + line + ", column " + col + "."; },
      detailInvalidGeneric: "Please check the syntax.",
      outputPlaceholder: "Paste a SQL query on the left to see the formatted result here.",
      errorBoxTitle: "This SQL query couldn't be parsed.",
      errorLocation: function (line, col) { return "Error location: around line " + line + ", column " + col; },
      unknownError: "Unknown error", regexError: "Regex error", copied: "Copied ✓",
      libMissing: "SQL formatting library failed to load. Please refresh the page.",
    },
    ko: {
      statusIdleText: "SQL 쿼리를 붙여넣어주세요", statusIdleTop: "대기 중",
      statusInvalidText: "SQL을 해석할 수 없습니다", statusInvalidTop: "무효",
      statusValidText: "정렬 완료", statusValidTop: "완료",
      detailInvalid: function (line, col) { return line + "행 " + col + "열 부근을 확인해주세요."; },
      detailInvalidGeneric: "구문을 확인해주세요.",
      outputPlaceholder: "왼쪽에 SQL 쿼리를 붙여넣으면 정렬된 결과가 여기에 표시됩니다.",
      errorBoxTitle: "이 SQL 쿼리를 해석할 수 없습니다.",
      errorLocation: function (line, col) { return "오류 위치: " + line + "번째 줄, " + col + "번째 열 부근"; },
      unknownError: "알 수 없는 오류", regexError: "정규식 오류", copied: "복사됨 ✓",
      libMissing: "SQL 정렬 라이브러리를 불러오지 못했습니다. 새로고침해주세요.",
    },
    ja: {
      statusIdleText: "SQLクエリを貼り付けてください", statusIdleTop: "待機中",
      statusInvalidText: "SQLを解析できませんでした", statusInvalidTop: "無効",
      statusValidText: "整形完了", statusValidTop: "完了",
      detailInvalid: function (line, col) { return line + "行目" + col + "列目付近をご確認ください。"; },
      detailInvalidGeneric: "構文をご確認ください。",
      outputPlaceholder: "左側にSQLクエリを貼り付けると、整形結果がここに表示されます。",
      errorBoxTitle: "このSQLクエリを解析できませんでした。",
      errorLocation: function (line, col) { return "エラー位置: " + line + "行目、" + col + "列目付近"; },
      unknownError: "不明なエラー", regexError: "正規表現エラー", copied: "コピーしました ✓",
      libMissing: "SQL整形ライブラリの読み込みに失敗しました。ページを再読み込みしてください。",
    },
    zh: {
      statusIdleText: "请粘贴 SQL 查询语句", statusIdleTop: "待处理",
      statusInvalidText: "无法解析该 SQL", statusInvalidTop: "无效",
      statusValidText: "格式化完成", statusValidTop: "完成",
      detailInvalid: function (line, col) { return "请检查第 " + line + " 行第 " + col + " 列附近。"; },
      detailInvalidGeneric: "请检查语法。",
      outputPlaceholder: "在左侧粘贴 SQL 查询语句，格式化结果将显示在这里。",
      errorBoxTitle: "无法解析该 SQL 查询语句。",
      errorLocation: function (line, col) { return "错误位置：第 " + line + " 行，第 " + col + " 列附近"; },
      unknownError: "未知错误", regexError: "正则表达式错误", copied: "已复制 ✓",
      libMissing: "SQL 格式化库加载失败，请刷新页面。",
    },
  };
  var T = MESSAGES[LANG];

  var els = {
    input: document.getElementById("sql-input"),
    status: document.getElementById("sql-status"),
    statusTop: document.getElementById("sql-status-top"),
    errorDetail: document.getElementById("sql-error-detail"),
    errorDetailTop: document.getElementById("sql-error-detail-top"),
    output: document.getElementById("sql-output"),
    gutter: document.getElementById("sql-gutter"),
    gutterInner: document.getElementById("sql-gutter-inner"),
    inputHighlight: document.getElementById("sql-input-highlight"),
    inputSearchMode: document.getElementById("sql-input-search-mode"),
    inputSearchInput: document.getElementById("sql-input-search"),
    inputSearchCount: document.getElementById("sql-input-search-count"),
    inputSearchPrev: document.getElementById("btn-input-search-prev"),
    inputSearchNext: document.getElementById("btn-input-search-next"),
    inputSearchClear: document.getElementById("btn-input-search-clear"),
    outputGutter: document.getElementById("sql-output-gutter"),
    outputGutterInner: document.getElementById("sql-output-gutter-inner"),
    tabInput: document.getElementById("tab-input"),
    tabOutput: document.getElementById("tab-output"),
    tabBadge: document.getElementById("tab-output-badge"),
    panelInput: document.getElementById("panel-input"),
    panelOutput: document.getElementById("panel-output"),
    btnFormat: document.getElementById("btn-format"),
    btnSample: document.getElementById("btn-sample"),
    btnClear: document.getElementById("btn-clear"),
    btnCopy: document.getElementById("btn-copy"),
    btnCopyMinify: document.getElementById("btn-copy-minify"),
    btnDownload: document.getElementById("btn-download"),
    indentSelect: document.getElementById("indent-select"),
    dialectSelect: document.getElementById("sql-dialect-select"),
    searchInput: document.getElementById("sql-search"),
    searchMode: document.getElementById("sql-search-mode"),
    searchPrev: document.getElementById("btn-search-prev"),
    searchNext: document.getElementById("btn-search-next"),
    searchClear: document.getElementById("btn-search-clear"),
  };

  if (!els.input) return; // 이 페이지가 아니면 아무 것도 하지 않음

  var state = {
    outputText: "",
    isValid: false,
    debounceTimer: null,
    inputMatches: [],
    inputActiveMatchIndex: -1,
  };

  var SAMPLE_SQL =
    "with recent_orders as (" +
    "select o.id, o.user_id, o.total, o.created_at from orders o where o.created_at >= '2026-01-01'" +
    "), user_totals as (" +
    "select user_id, sum(total) as total_spent, count(*) as order_count from recent_orders group by user_id" +
    ") " +
    "select u.id, u.name, u.email, ut.total_spent, ut.order_count, " +
    "case when ut.total_spent >= 1000 then 'gold' when ut.total_spent >= 500 then 'silver' else 'bronze' end as tier " +
    "from users u " +
    "inner join user_totals ut on ut.user_id = u.id " +
    "left join addresses a on a.user_id = u.id and a.is_primary = true " +
    "where u.status = 'active' " +
    "and exists (select 1 from subscriptions s where s.user_id = u.id and s.active = true) " +
    "order by ut.total_spent desc limit 50;";

  // ---------------------------------------------------------------
  // 1. 들여쓰기 / 방언 옵션
  // ---------------------------------------------------------------

  function getIndentOptions() {
    var v = els.indentSelect.value;
    if (v === "tab") return { useTabs: true };
    return { tabWidth: parseInt(v, 10), useTabs: false };
  }

  function getDialect() {
    return els.dialectSelect ? els.dialectSelect.value : "sql";
  }

  // ---------------------------------------------------------------
  // 2. 실행 파이프라인
  // ---------------------------------------------------------------

  function locateSqlErrorPosition(message) {
    var m = /at line (\d+) column (\d+)/i.exec(message || "");
    if (m) return { line: parseInt(m[1], 10), column: parseInt(m[2], 10) };
    return null;
  }

  function formatSql(text) {
    var opts = getIndentOptions();
    opts.language = getDialect();
    opts.keywordCase = "upper";
    return window.sqlFormatter.format(text, opts);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ---------------------------------------------------------------
  // 1-1. 출력 문법 강조
  // ---------------------------------------------------------------

  var SQL_KEYWORDS = (
    "SELECT FROM WHERE JOIN INNER LEFT RIGHT FULL OUTER CROSS ON AS AND OR NOT NULL IS IN EXISTS " +
    "BETWEEN LIKE ILIKE GROUP BY ORDER HAVING LIMIT OFFSET DISTINCT UNION ALL INTERSECT EXCEPT " +
    "INSERT INTO VALUES UPDATE SET DELETE CREATE TABLE ALTER DROP VIEW INDEX IF FUNCTION PROCEDURE TRIGGER " +
    "CASE WHEN THEN ELSE END ASC DESC WITH OVER PARTITION WINDOW RECURSIVE " +
    "PRIMARY KEY FOREIGN REFERENCES DEFAULT CONSTRAINT UNIQUE CHECK CASCADE " +
    "BEGIN COMMIT ROLLBACK TRANSACTION GRANT REVOKE TRUE FALSE"
  ).split(/\s+/);
  var SQL_KEYWORD_SET = {};
  SQL_KEYWORDS.forEach(function (k) {
    SQL_KEYWORD_SET[k] = true;
  });

  function highlightSqlText(text) {
    var re =
      /(--[^\n]*)|(\/\*[\s\S]*?\*\/)|('(?:[^'\\]|\\.|'')*')|("(?:[^"\\]|\\.)*")|(\b\d+(?:\.\d+)?\b)|(\b[A-Za-z_][A-Za-z0-9_]*\b)|([(),;.])/g;
    var html = "";
    var cursor = 0;
    var m;
    while ((m = re.exec(text)) !== null) {
      html += escapeHtml(text.slice(cursor, m.index));
      var tok = m[0];
      if (m[1] || m[2]) {
        html += '<span class="sql-comment">' + escapeHtml(tok) + "</span>";
      } else if (m[3] || m[4]) {
        html += '<span class="sql-string">' + escapeHtml(tok) + "</span>";
      } else if (m[5]) {
        html += '<span class="sql-number">' + escapeHtml(tok) + "</span>";
      } else if (m[6]) {
        html += SQL_KEYWORD_SET[tok] ? '<span class="sql-keyword">' + tok + "</span>" : escapeHtml(tok);
      } else if (m[7]) {
        html += '<span class="sql-punct">' + escapeHtml(tok) + "</span>";
      } else {
        html += escapeHtml(tok);
      }
      cursor = m.index + tok.length;
    }
    html += escapeHtml(text.slice(cursor));
    return html;
  }

  function renderOutputText(text) {
    els.output.innerHTML = '<pre class="sql-output-text"></pre>';
    els.output.firstChild.innerHTML = highlightSqlText(text);
    renderOutputGutter(text);
  }

  function renderPlaceholder() {
    els.output.innerHTML = '<p class="jf-placeholder">' + escapeHtml(T.outputPlaceholder) + "</p>";
    renderOutputGutter("");
  }

  function renderErrorBox(message, loc) {
    var lines = [];
    lines.push("<p><strong>" + escapeHtml(T.errorBoxTitle) + "</strong></p>");
    if (loc) {
      lines.push("<p>" + escapeHtml(T.errorLocation(loc.line, loc.column)) + "</p>");
    }
    var firstLine = (message || T.unknownError).split("\n")[0];
    lines.push("<p><code>" + escapeHtml(firstLine) + "</code></p>");
    els.output.innerHTML = '<div class="jf-error-box">' + lines.join("") + "</div>";
    renderOutputGutter("");
  }

  function renderOutputGutter(text) {
    if (!els.outputGutterInner) return;
    var lineCount = text.length === 0 ? 1 : text.split("\n").length;
    var frag = document.createDocumentFragment();
    for (var n = 1; n <= lineCount; n++) {
      var lineEl = document.createElement("div");
      lineEl.className = "jf-gutter-line";
      var numberEl = document.createElement("span");
      numberEl.className = "jf-gutter-number";
      numberEl.textContent = String(n);
      lineEl.appendChild(numberEl);
      frag.appendChild(lineEl);
    }
    els.outputGutterInner.innerHTML = "";
    els.outputGutterInner.appendChild(frag);
  }

  if (els.output) {
    els.output.addEventListener("scroll", function () {
      if (els.outputGutterInner) {
        els.outputGutterInner.style.transform = "translateY(-" + els.output.scrollTop + "px)";
      }
    });
  }

  function setStatus(kind, text, topText, detailText) {
    els.status.className = "status-pill is-" + kind;
    els.status.textContent = text;
    if (els.statusTop) {
      els.statusTop.className = "status-pill is-" + kind;
      els.statusTop.textContent = topText || text;
    }
    if (els.tabBadge) els.tabBadge.className = "jf-tab-badge is-" + kind;
    var detail = detailText || "";
    els.errorDetail.textContent = detail;
    if (els.errorDetailTop) els.errorDetailTop.textContent = detail;
  }

  function setToolbarEnabled(enabled) {
    [els.btnCopy, els.btnCopyMinify, els.btnDownload].forEach(function (el) {
      if (el) el.disabled = !enabled;
    });
  }

  function process() {
    var text = els.input.value;

    if (text.trim() === "") {
      state.isValid = false;
      state.outputText = "";
      setStatus("idle", T.statusIdleText, T.statusIdleTop);
      renderPlaceholder();
      renderGutter(text);
      setToolbarEnabled(false);
      return;
    }

    if (!window.sqlFormatter || typeof window.sqlFormatter.format !== "function") {
      state.isValid = false;
      setStatus("invalid", T.libMissing, T.statusInvalidTop);
      renderErrorBox(T.libMissing, null);
      renderGutter(text);
      setToolbarEnabled(false);
      return;
    }

    try {
      var formatted = formatSql(text);
      state.isValid = true;
      state.outputText = formatted;
      setStatus("valid", T.statusValidText, T.statusValidTop);
      renderGutter(text);
      renderOutputText(formatted);
      setToolbarEnabled(true);
    } catch (e) {
      state.isValid = false;
      state.outputText = "";
      var loc = locateSqlErrorPosition(e && e.message);
      var detail = loc ? T.detailInvalid(loc.line, loc.column) : T.detailInvalidGeneric;
      setStatus("invalid", T.statusInvalidText, T.statusInvalidTop, detail);
      renderErrorBox(e && e.message, loc);
      renderGutter(text);
      setToolbarEnabled(false);
    }
  }

  function scheduleProcess() {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(function () {
      process();
    }, 300);
  }

  // ---------------------------------------------------------------
  // 3. 입력창 줄 번호
  // ---------------------------------------------------------------

  function renderGutter(text) {
    var lineCount = text.length === 0 ? 1 : text.split("\n").length;
    var frag = document.createDocumentFragment();
    for (var n = 1; n <= lineCount; n++) {
      var lineEl = document.createElement("div");
      lineEl.className = "jf-gutter-line";
      var numberEl = document.createElement("span");
      numberEl.className = "jf-gutter-number";
      numberEl.textContent = String(n);
      lineEl.appendChild(numberEl);
      frag.appendChild(lineEl);
    }
    els.gutterInner.innerHTML = "";
    els.gutterInner.appendChild(frag);
  }

  els.input.addEventListener("scroll", function () {
    els.gutterInner.style.transform = "translateY(-" + els.input.scrollTop + "px)";
    if (els.inputHighlight) {
      els.inputHighlight.style.transform =
        "translate(-" + els.input.scrollLeft + "px, -" + els.input.scrollTop + "px)";
    }
  });

  els.input.addEventListener("input", function () {
    renderGutter(els.input.value);
    refreshInputSearchOverlay();
  });

  // ---------------------------------------------------------------
  // 4. 입력창 검색
  // ---------------------------------------------------------------

  function computeTextMatchRanges(text, mode, query) {
    if (!query) return [];

    if (mode === "contains") {
      var ranges = [];
      var lower = text.toLowerCase();
      var q = query.toLowerCase();
      var idx = lower.indexOf(q);
      while (idx !== -1) {
        ranges.push([idx, idx + q.length]);
        idx = lower.indexOf(q, idx + q.length);
      }
      return ranges;
    }

    if (mode === "exact") {
      var exactRanges = [];
      var trimmedQuery = query.trim().toLowerCase();
      if (!trimmedQuery) return [];
      var offset = 0;
      text.split("\n").forEach(function (line) {
        if (line.trim().toLowerCase() === trimmedQuery) {
          var leading = line.length - line.replace(/^\s+/, "").length;
          var trailing = line.length - line.replace(/\s+$/, "").length;
          exactRanges.push([offset + leading, offset + line.length - trailing]);
        }
        offset += line.length + 1;
      });
      return exactRanges;
    }

    if (mode === "regex") {
      var re = new RegExp(query, "gim");
      var regexRanges = [];
      var m;
      while ((m = re.exec(text)) !== null) {
        if (m[0].length === 0) {
          re.lastIndex++;
          continue;
        }
        regexRanges.push([m.index, m.index + m[0].length]);
      }
      return regexRanges;
    }

    return [];
  }

  function buildFullTextHighlightHtml(text, ranges, activeIndex) {
    if (!ranges.length) return escapeHtml(text);
    var html = "";
    var cursor = 0;
    ranges.forEach(function (r, idx) {
      html += escapeHtml(text.slice(cursor, r[0]));
      var cls = "json-search-match" + (idx === activeIndex ? " is-active" : "");
      html += '<mark class="' + cls + '">' + escapeHtml(text.slice(r[0], r[1])) + "</mark>";
      cursor = r[1];
    });
    html += escapeHtml(text.slice(cursor));
    return html;
  }

  function renderInputHighlight() {
    if (!els.inputHighlight) return;
    var html = buildFullTextHighlightHtml(els.input.value, state.inputMatches, state.inputActiveMatchIndex);
    els.inputHighlight.innerHTML = html;
  }

  function updateInputSearchCount(errorMessage) {
    if (!els.inputSearchCount) return;
    if (errorMessage) {
      els.inputSearchCount.textContent = errorMessage;
      els.inputSearchCount.classList.add("has-error");
      return;
    }
    els.inputSearchCount.classList.remove("has-error");
    if (state.inputMatches.length === 0) {
      els.inputSearchCount.textContent = "0 / 0";
    } else {
      els.inputSearchCount.textContent = state.inputActiveMatchIndex + 1 + " / " + state.inputMatches.length;
    }
  }

  function updateInputSearchButtons() {
    if (!els.inputSearchClear) return;
    var hasQuery = els.inputSearchInput.value.length > 0;
    var hasMatches = state.inputMatches.length > 0;
    els.inputSearchClear.disabled = !hasQuery;
    els.inputSearchPrev.disabled = !hasMatches;
    els.inputSearchNext.disabled = !hasMatches;
  }

  function computeAndRenderInputMatches() {
    var mode = els.inputSearchMode.value;
    var query = els.inputSearchInput.value;
    var text = els.input.value;

    var regexError = null;
    if (mode === "regex" && query) {
      try {
        new RegExp(query, "gim");
      } catch (e) {
        regexError = e;
      }
    }
    els.inputSearchInput.classList.toggle("has-error", !!regexError);

    var ranges = [];
    if (query && !regexError) {
      try {
        ranges = computeTextMatchRanges(text, mode, query);
      } catch (e) {
        ranges = [];
      }
    }

    state.inputMatches = ranges;
    if (state.inputActiveMatchIndex >= ranges.length) {
      state.inputActiveMatchIndex = ranges.length > 0 ? 0 : -1;
    }
    if (state.inputActiveMatchIndex < 0 && ranges.length > 0) {
      state.inputActiveMatchIndex = 0;
    }

    renderInputHighlight();
    updateInputSearchCount(regexError ? T.regexError : null);
    updateInputSearchButtons();
  }

  function refreshInputSearchOverlay() {
    if (!els.inputSearchInput) return;
    if (els.inputSearchInput.value) {
      computeAndRenderInputMatches();
    } else {
      state.inputMatches = [];
      state.inputActiveMatchIndex = -1;
      renderInputHighlight();
      updateInputSearchButtons();
    }
  }

  function scrollTextareaToOffset(textarea, offset) {
    var textBefore = textarea.value.slice(0, offset);
    var lineNumber = textBefore.split("\n").length;
    var computed = window.getComputedStyle(textarea);
    var lineHeight = parseFloat(computed.lineHeight);
    if (!lineHeight || isNaN(lineHeight)) lineHeight = 21.8;
    var target = (lineNumber - 1) * lineHeight - textarea.clientHeight / 2 + lineHeight / 2;
    target = Math.max(0, Math.min(target, textarea.scrollHeight - textarea.clientHeight));
    textarea.scrollTop = target;
  }

  function selectInputMatch(index, scrollIntoView) {
    var range = state.inputMatches[index];
    if (!range) return;
    if (document.activeElement === els.input) {
      els.input.setSelectionRange(range[0], range[1]);
    }
    if (scrollIntoView) {
      scrollTextareaToOffset(els.input, range[0]);
    }
  }

  function goToInputMatch(delta) {
    if (state.inputMatches.length === 0) return;
    state.inputActiveMatchIndex =
      (state.inputActiveMatchIndex + delta + state.inputMatches.length) % state.inputMatches.length;
    renderInputHighlight();
    updateInputSearchCount();
    selectInputMatch(state.inputActiveMatchIndex, true);
  }

  if (els.inputSearchInput) {
    var inputSearchDebounce = null;
    els.inputSearchInput.addEventListener("input", function () {
      clearTimeout(inputSearchDebounce);
      inputSearchDebounce = setTimeout(function () {
        computeAndRenderInputMatches();
        if (state.inputActiveMatchIndex >= 0) {
          selectInputMatch(state.inputActiveMatchIndex, true);
        }
      }, 150);
    });

    els.inputSearchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        var targetBtn = e.shiftKey ? els.inputSearchPrev : els.inputSearchNext;
        if (targetBtn && !targetBtn.disabled) targetBtn.click();
      }
    });

    els.inputSearchMode.addEventListener("change", function () {
      computeAndRenderInputMatches();
      if (state.inputActiveMatchIndex >= 0) selectInputMatch(state.inputActiveMatchIndex, true);
    });

    els.inputSearchPrev.addEventListener("click", function () {
      goToInputMatch(-1);
    });
    els.inputSearchNext.addEventListener("click", function () {
      goToInputMatch(1);
    });
    els.inputSearchClear.addEventListener("click", function () {
      els.inputSearchInput.value = "";
      els.inputSearchInput.classList.remove("has-error");
      state.inputMatches = [];
      state.inputActiveMatchIndex = -1;
      renderInputHighlight();
      updateInputSearchCount();
      updateInputSearchButtons();
      els.inputSearchInput.focus();
    });
  }

  // ---------------------------------------------------------------
  // 5. 툴바 동작
  // ---------------------------------------------------------------

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
    } catch (e) {
      /* noop */
    }
    document.body.removeChild(ta);
    return Promise.resolve();
  }

  function flashButton(btn, tempLabel) {
    var original = btn.textContent;
    btn.textContent = tempLabel;
    setTimeout(function () {
      btn.textContent = original;
    }, 1200);
  }

  els.input.addEventListener("input", scheduleProcess);

  els.btnFormat.addEventListener("click", function () {
    clearTimeout(state.debounceTimer);
    process();
    refreshInputSearchOverlay();
    if (state.isValid) switchTab("output");
  });

  els.btnSample.addEventListener("click", function () {
    els.input.value = SAMPLE_SQL;
    process();
    refreshInputSearchOverlay();
  });

  els.btnClear.addEventListener("click", function () {
    els.input.value = "";
    els.input.focus();
    process();
    refreshInputSearchOverlay();
  });

  if (els.dialectSelect) {
    els.dialectSelect.addEventListener("change", function () {
      process();
    });
  }

  els.btnCopy.addEventListener("click", function () {
    if (!state.isValid) return;
    copyToClipboard(state.outputText);
    flashButton(els.btnCopy, T.copied);
  });

  els.btnCopyMinify.addEventListener("click", function () {
    if (!state.isValid || !window.sqlFormatter) return;
    var minified;
    try {
      minified = window.sqlFormatter.format(els.input.value, {
        language: getDialect(),
        keywordCase: "upper",
        tabWidth: 0,
        linesBetweenQueries: 0,
      }).replace(/\n/g, " ").replace(/\s{2,}/g, " ").trim();
    } catch (e) {
      minified = state.outputText;
    }
    copyToClipboard(minified);
    flashButton(els.btnCopyMinify, T.copied);
  });

  els.btnDownload.addEventListener("click", function () {
    if (!state.isValid) return;
    var blob = new Blob([state.outputText], { type: "text/plain" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "formatted.sql";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // ---------------------------------------------------------------
  // 6. 탭 전환
  // ---------------------------------------------------------------

  function switchTab(tab) {
    var showInput = tab === "input";
    els.tabInput.classList.toggle("is-active", showInput);
    els.tabOutput.classList.toggle("is-active", !showInput);
    els.tabInput.setAttribute("aria-selected", String(showInput));
    els.tabOutput.setAttribute("aria-selected", String(!showInput));
    els.panelInput.hidden = !showInput;
    els.panelOutput.hidden = showInput;
  }

  els.tabInput.addEventListener("click", function () {
    switchTab("input");
  });
  els.tabOutput.addEventListener("click", function () {
    switchTab("output");
  });

  // ---------------------------------------------------------------
  // 7. 초기화
  // ---------------------------------------------------------------

  els.input.value = SAMPLE_SQL;
  setToolbarEnabled(false);
  process();
  refreshInputSearchOverlay();
})();
