/**
 * JSON 포매터 / 뷰어
 * - 입력한 문자열이 유효한 JSON인지 검사
 * - 들여쓰기 + 문법 강조가 적용된 트리 형태로 렌더링
 * - 노드별 접기/펼치기, 전체 펼치기/접기
 * - 키/값 텍스트 검색 (이전/다음 이동, 일치 개수 표시)
 *
 * 입력값은 서버로 전송되지 않고 이 파일 안에서만(브라우저 내에서) 처리됩니다.
 */
(function () {
  "use strict";

  var els = {
    input: document.getElementById("json-input"),
    status: document.getElementById("json-status"),
    statusTop: document.getElementById("json-status-top"),
    errorDetail: document.getElementById("json-error-detail"),
    errorDetailTop: document.getElementById("json-error-detail-top"),
    output: document.getElementById("json-output"),
    gutter: document.getElementById("json-gutter"),
    gutterInner: document.getElementById("json-gutter-inner"),
    inputHighlight: document.getElementById("json-input-highlight"),
    inputSearchMode: document.getElementById("json-input-search-mode"),
    inputSearchInput: document.getElementById("json-input-search"),
    inputSearchCount: document.getElementById("json-input-search-count"),
    inputSearchPrev: document.getElementById("btn-input-search-prev"),
    inputSearchNext: document.getElementById("btn-input-search-next"),
    inputSearchClear: document.getElementById("btn-input-search-clear"),
    outputGutter: document.getElementById("json-output-gutter"),
    outputGutterInner: document.getElementById("json-output-gutter-inner"),
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
    btnExpandAll: document.getElementById("btn-expand-all"),
    btnCollapseAll: document.getElementById("btn-collapse-all"),
    searchInput: document.getElementById("json-search"),
    searchMode: document.getElementById("json-search-mode"),
    searchCount: document.getElementById("jf-search-count"),
    searchPrev: document.getElementById("btn-search-prev"),
    searchNext: document.getElementById("btn-search-next"),
    searchClear: document.getElementById("btn-search-clear"),
  };

  var state = {
    parsedValue: undefined,
    isValid: false,
    debounceTimer: null,
    matches: [],
    activeMatchIndex: -1,
    lastCorrectedLines: new Set(),
    inputMatches: [],
    inputActiveMatchIndex: -1,
  };

  // 각 접이식 노드(wrapper)와 그 토글 버튼을 연결해두는 맵.
  // 토글 버튼은 행(row) 안이 아니라 결과 줄 번호 옆(거터)에 배치되므로,
  // 트리를 다시 그릴 때마다 초기화하고 renderOutputGutter()가 이 맵을 참조해
  // 현재 보이는 줄에 맞는 버튼을 이동시켜 넣는다.
  var toggleRegistry = new Map();

  var SAMPLE_JSON = JSON.stringify(
    {
      id: 1024,
      name: "웹툴박스",
      isActive: true,
      rating: 4.8,
      tags: ["json", "formatter", "viewer"],
      owner: { email: "hongsh119@gmail.com", verified: true },
      children: [],
      note: null,
    },
    null,
    2
  );

  // ---------------------------------------------------------------
  // 1. 파싱 / 유효성 검사
  // ---------------------------------------------------------------

  function locateErrorPosition(text, message) {
    var match = /position (\d+)/.exec(message || "");
    if (!match) return null;
    var pos = parseInt(match[1], 10);
    var upTo = text.slice(0, pos);
    var lines = upTo.split("\n");
    return {
      pos: pos,
      line: lines.length,
      column: lines[lines.length - 1].length + 1,
    };
  }

  /**
   * 관대한(lenient) JSON 파서
   * - 키/문자열 값의 큰따옴표(또는 작은따옴표)가 없어도 최대한 값을 읽어들인다.
   * - 따옴표 없는 값은 콤마(,) 또는 닫는 괄호(}, ]) 앞까지를 값으로 간주해 트리밍한다.
   * - true/false/null, 숫자는 그대로 해당 타입으로 변환하고, 그 외에는 문자열로 처리한다.
   * - 여는 괄호와 닫는 괄호 앞의 불필요한 콤마(trailing comma)도 허용한다.
   * 정상적인 JSON도 항상 이 파서로 파싱 가능하지만, 우선 표준 JSON.parse를 먼저 시도해
   * 에러 위치를 정확히 안내한 뒤, 실패했을 때만 이 파서로 복구를 시도한다.
   */
  function parseLenientJSON(text) {
    var i = 0;
    var len = text.length;
    var correctedLines = new Set();

    function isWs(c) {
      return c === " " || c === "\t" || c === "\n" || c === "\r";
    }
    function skipWs() {
      while (i < len && isWs(text[i])) i++;
    }
    function fail(msg) {
      var e = new Error(msg);
      e.lenientPos = i;
      throw e;
    }
    function isStopChar(c) {
      return c === "," || c === "}" || c === "]" || c === undefined;
    }
    function lineAt(pos) {
      return text.slice(0, pos).split("\n").length;
    }
    function markCorrected(startPos, endPos) {
      var from = lineAt(startPos);
      var to = lineAt(endPos);
      for (var l = from; l <= to; l++) correctedLines.add(l);
    }
    // 앞뒤 공백/개행을 뺀 실제 토큰 범위를 구한다 (trim으로 사라지는 개행이
    // 줄 강조 범위에 섞여 다음 줄까지 잘못 표시되는 것을 방지).
    function trimmedRange(start, end, raw) {
      var leading = raw.length - raw.replace(/^\s+/, "").length;
      var trailing = raw.length - raw.replace(/\s+$/, "").length;
      return { start: start + leading, end: end - trailing };
    }

    function parseQuoted(quote) {
      i++; // opening quote
      var out = "";
      var escapeMap = { '"': '"', "'": "'", "\\": "\\", "/": "/", b: "\b", f: "\f", n: "\n", r: "\r", t: "\t" };
      while (i < len) {
        var c = text[i];
        if (c === quote) {
          i++;
          return out;
        }
        if (c === "\\") {
          var next = text[i + 1];
          if (next === "u") {
            var hex = text.slice(i + 2, i + 6);
            out += String.fromCharCode(parseInt(hex, 16));
            i += 6;
          } else if (Object.prototype.hasOwnProperty.call(escapeMap, next)) {
            out += escapeMap[next];
            i += 2;
          } else {
            out += next;
            i += 2;
          }
          continue;
        }
        out += c;
        i++;
      }
      return out; // 닫는 따옴표가 없으면 끝까지를 문자열로 간주 (best-effort)
    }

    function interpretBareToken(token) {
      if (token === "true") return true;
      if (token === "false") return false;
      if (token === "null") return null;
      if (/^-?\d+(\.\d+)?([eE][+-]?\d+)?$/.test(token)) return Number(token);
      return token; // 따옴표 없는 문자열 값
    }

    function parseBareValue() {
      var start = i;
      while (i < len && !isStopChar(text[i])) i++;
      var end = i;
      var rawFull = text.slice(start, end);
      var raw = rawFull.trim();
      if (raw === "") fail("값이 비어 있습니다.");
      var value = interpretBareToken(raw);
      if (typeof value === "string") {
        // true/false/null/숫자가 아닌 순수 문자열 값만 "따옴표 보정"으로 간주한다.
        var range = trimmedRange(start, end, rawFull);
        markCorrected(range.start, range.end);
      }
      return value;
    }

    function parseBareKey() {
      var start = i;
      while (i < len && text[i] !== ":") i++;
      if (i >= len) fail("키 뒤에 ':'가 필요합니다.");
      var end = i;
      var rawFull = text.slice(start, end);
      var raw = rawFull.trim();
      if (raw === "") fail("키가 비어 있습니다.");
      var range = trimmedRange(start, end, rawFull);
      markCorrected(range.start, range.end);
      return raw;
    }

    function parseKey() {
      skipWs();
      var c = text[i];
      if (c === '"' || c === "'") return parseQuoted(c);
      return parseBareKey();
    }

    function parseValue() {
      skipWs();
      if (i >= len) fail("값이 필요합니다.");
      var c = text[i];
      if (c === "{") return parseObject();
      if (c === "[") return parseArray();
      if (c === '"' || c === "'") return parseQuoted(c);
      return parseBareValue();
    }

    function parseObject() {
      i++; // '{'
      var obj = {};
      skipWs();
      if (text[i] === "}") {
        i++;
        return obj;
      }
      while (true) {
        skipWs();
        var key = parseKey();
        skipWs();
        if (text[i] !== ":") fail("키 다음에 ':'가 필요합니다.");
        i++;
        skipWs();
        obj[key] = parseValue();
        skipWs();
        if (text[i] === ",") {
          i++;
          skipWs();
          if (text[i] === "}") {
            i++;
            break;
          }
          continue;
        }
        if (text[i] === "}") {
          i++;
          break;
        }
        fail("',' 또는 '}' 가 필요합니다.");
      }
      return obj;
    }

    function parseArray() {
      i++; // '['
      var arr = [];
      skipWs();
      if (text[i] === "]") {
        i++;
        return arr;
      }
      while (true) {
        skipWs();
        arr.push(parseValue());
        skipWs();
        if (text[i] === ",") {
          i++;
          skipWs();
          if (text[i] === "]") {
            i++;
            break;
          }
          continue;
        }
        if (text[i] === "]") {
          i++;
          break;
        }
        fail("',' 또는 ']' 가 필요합니다.");
      }
      return arr;
    }

    skipWs();
    var result = parseValue();
    skipWs();
    if (i < len) fail("입력 끝부분에 처리할 수 없는 문자가 있습니다.");
    return { value: result, correctedLines: correctedLines };
  }

  function tryParse(text) {
    if (text.trim() === "") {
      return { ok: false, empty: true };
    }
    try {
      var value = JSON.parse(text);
      return { ok: true, value: value, mode: "strict" };
    } catch (strictErr) {
      try {
        var lenient = parseLenientJSON(text);
        return { ok: true, value: lenient.value, mode: "lenient", correctedLines: lenient.correctedLines };
      } catch (lenientErr) {
        return { ok: false, message: strictErr.message, loc: locateErrorPosition(text, strictErr.message) };
      }
    }
  }

  // ---------------------------------------------------------------
  // 2. 트리 렌더링
  // ---------------------------------------------------------------

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function createToggle(node) {
    var toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "json-toggle";
    toggle.textContent = "▾";
    toggle.setAttribute("aria-label", "노드 접기/펼치기");
    toggle.setAttribute("aria-expanded", "true");
    toggle.addEventListener("click", function () {
      var collapsed = node.classList.toggle("is-collapsed");
      toggle.textContent = collapsed ? "▸" : "▾";
      toggle.setAttribute("aria-expanded", String(!collapsed));
      renderOutputGutter();
    });
    return toggle;
  }

  /**
   * key: 문자열 key, 숫자 index, 또는 null(값만 있는 경우/루트)
   * value: 렌더링할 값
   * isLast: 부모 컨테이너 안에서 마지막 항목인지 (콤마 표시 여부)
   */
  function buildNode(key, value, isLast) {
    var wrapper = document.createElement("div");
    wrapper.className = "json-node";

    var row = document.createElement("div");
    row.className = "json-row";
    wrapper.appendChild(row);

    if (key !== null) {
      var keySpan = document.createElement("span");
      keySpan.className = "json-key";
      var keyText = JSON.stringify(String(key));
      keySpan.textContent = keyText;
      keySpan.dataset.raw = keyText;
      row.appendChild(keySpan);

      var colon = document.createElement("span");
      colon.className = "json-punct";
      colon.textContent = ": ";
      row.appendChild(colon);
    }

    var isContainer = value !== null && typeof value === "object";

    if (isContainer) {
      var isArray = Array.isArray(value);
      var entries = isArray ? value.map(function (v, i) { return [i, v]; }) : Object.keys(value).map(function (k) { return [k, value[k]]; });
      var openChar = isArray ? "[" : "{";
      var closeChar = isArray ? "]" : "}";

      if (entries.length === 0) {
        var emptySpan = document.createElement("span");
        emptySpan.className = "json-bracket";
        emptySpan.textContent = openChar + closeChar;
        row.appendChild(emptySpan);
        if (!isLast) appendComma(row);
        return wrapper;
      }

      wrapper.classList.add("is-collapsible");
      // 접기/펼치기 버튼은 줄 안에 넣지 않고, 결과 줄 번호 옆(거터)에 배치한다.
      toggleRegistry.set(wrapper, createToggle(wrapper));

      var openSpan = document.createElement("span");
      openSpan.className = "json-bracket";
      openSpan.textContent = openChar;
      row.appendChild(openSpan);

      var previewSpan = document.createElement("span");
      previewSpan.className = "json-preview";
      previewSpan.textContent =
        " … " + entries.length + (isArray ? "개 항목" : "개 키") + " " + closeChar + (isLast ? "" : ",");
      row.appendChild(previewSpan);

      var childrenWrap = document.createElement("div");
      childrenWrap.className = "json-children";
      entries.forEach(function (pair, idx) {
        var childKey = isArray ? null : pair[0];
        var childVal = pair[1];
        var childIsLast = idx === entries.length - 1;
        childrenWrap.appendChild(buildNode(childKey, childVal, childIsLast));
      });
      wrapper.appendChild(childrenWrap);

      var closeRow = document.createElement("div");
      closeRow.className = "json-row json-close-row";
      var closeSpan = document.createElement("span");
      closeSpan.className = "json-bracket";
      closeSpan.textContent = closeChar;
      closeRow.appendChild(closeSpan);
      if (!isLast) appendComma(closeRow);
      wrapper.appendChild(closeRow);

      return wrapper;
    }

    // 원시값 (string / number / boolean / null)
    var valueSpan = document.createElement("span");
    var cls, text;
    if (value === null) {
      cls = "json-null";
      text = "null";
    } else if (typeof value === "string") {
      cls = "json-string";
      text = JSON.stringify(value);
    } else if (typeof value === "number") {
      cls = "json-number";
      text = String(value);
    } else if (typeof value === "boolean") {
      cls = "json-boolean";
      text = String(value);
    } else {
      cls = "json-null";
      text = String(value);
    }
    valueSpan.className = cls + " json-value";
    valueSpan.textContent = text;
    valueSpan.dataset.raw = text;
    row.appendChild(valueSpan);
    if (!isLast) appendComma(row);

    return wrapper;
  }

  function appendComma(row) {
    var comma = document.createElement("span");
    comma.className = "json-punct";
    comma.textContent = ",";
    row.appendChild(comma);
  }

  function renderTree(value) {
    toggleRegistry = new Map();
    els.output.innerHTML = "";
    var treeRoot = document.createElement("div");
    treeRoot.className = "json-tree";
    treeRoot.appendChild(buildNode(null, value, true));
    els.output.appendChild(treeRoot);
    renderOutputGutter();
  }

  function renderPlaceholder() {
    els.output.innerHTML = '<p class="jf-placeholder">왼쪽에 JSON 문자열을 입력하면 결과가 여기에 표시됩니다.</p>';
    renderOutputGutter();
  }

  function renderErrorBox(parsed, rawText) {
    var lines = [];
    lines.push("<p><strong>JSON 형식이 올바르지 않습니다.</strong></p>");
    if (parsed.loc) {
      lines.push("<p>오류 위치: " + parsed.loc.line + "번째 줄, " + parsed.loc.column + "번째 문자 부근</p>");
    }
    lines.push("<p><code>" + escapeHtml(parsed.message || "알 수 없는 오류") + "</code></p>");
    els.output.innerHTML = '<div class="jf-error-box">' + lines.join("") + "</div>";
    renderOutputGutter();
  }

  // ---------------------------------------------------------------
  // 2-1. 결과 화면 줄 번호 (접기/펼치기 상태에 따라 보이는 줄만 다시 매김)
  // ---------------------------------------------------------------

  /**
   * 화면에 보이는 순서대로 { row, node } 목록을 만든다.
   * node는 해당 줄이 접기/펼치기가 가능한 객체/배열의 "머리글 줄"일 때만 채워지고,
   * 닫는 괄호 줄이나 원시값 줄은 node가 null이다 (토글이 필요 없으므로).
   */
  function collectVisibleOutputRows() {
    var treeRoot = els.output.querySelector(".json-tree");
    var items = [];
    if (!treeRoot) return items;

    function walkNode(node) {
      var row = node.querySelector(":scope > .json-row:not(.json-close-row)");
      if (row) items.push({ row: row, node: node.classList.contains("is-collapsible") ? node : null });
      if (!node.classList.contains("is-collapsed")) {
        var childrenWrap = node.querySelector(":scope > .json-children");
        if (childrenWrap) {
          Array.prototype.forEach.call(childrenWrap.children, function (child) {
            if (child.classList.contains("json-node")) walkNode(child);
          });
        }
        var closeRow = node.querySelector(":scope > .json-close-row");
        if (closeRow) items.push({ row: closeRow, node: null });
      }
    }

    Array.prototype.forEach.call(treeRoot.children, function (child) {
      if (child.classList.contains("json-node")) walkNode(child);
    });
    return items;
  }

  function renderOutputGutter() {
    if (!els.outputGutterInner) return;
    var items = collectVisibleOutputRows();
    var frag = document.createDocumentFragment();
    items.forEach(function (item, idx) {
      var lineEl = document.createElement("div");
      lineEl.className = "jf-gutter-line";

      var toggleSlot = document.createElement("span");
      toggleSlot.className = "jf-gutter-toggle-slot";
      var toggle = item.node ? toggleRegistry.get(item.node) : null;
      if (toggle) toggleSlot.appendChild(toggle); // 기존 버튼(과 클릭 핸들러)을 그대로 이동
      lineEl.appendChild(toggleSlot);

      var numberEl = document.createElement("span");
      numberEl.className = "jf-gutter-number";
      numberEl.textContent = String(idx + 1);
      lineEl.appendChild(numberEl);

      frag.appendChild(lineEl);
    });
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

  // ---------------------------------------------------------------
  // 3. 상태 표시 (유효/무효 배지)
  // ---------------------------------------------------------------

  function setStatus(kind, text, topText, detailText) {
    els.status.className = "status-pill is-" + kind;
    els.status.textContent = text;
    if (els.statusTop) {
      els.statusTop.className = "status-pill is-" + kind;
      els.statusTop.textContent = topText || text;
    }
    if (els.tabBadge) {
      els.tabBadge.className = "jf-tab-badge is-" + kind;
    }
    var detail = detailText || "";
    els.errorDetail.textContent = detail;
    if (els.errorDetailTop) els.errorDetailTop.textContent = detail;
  }

  // ---------------------------------------------------------------
  // 3-1. 줄 번호 표시 (입력 영역)
  // ---------------------------------------------------------------

  function renderGutter(text, correctedLines) {
    var lineCount = text.length === 0 ? 1 : text.split("\n").length;
    var frag = document.createDocumentFragment();
    for (var n = 1; n <= lineCount; n++) {
      var lineEl = document.createElement("div");
      lineEl.className = "jf-gutter-line" + (correctedLines && correctedLines.has(n) ? " is-corrected" : "");
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

  // 줄 번호 자체는 유효성 검사와 무관하게 타이핑 즉시 갱신한다 (보정 표시는 검증 후 갱신).
  // 입력 검색 강조 오버레이도 텍스트가 바뀔 때마다 최신 내용으로 다시 그린다(커서/선택은 건드리지 않음).
  els.input.addEventListener("input", function () {
    renderGutter(els.input.value, state.lastCorrectedLines);
    refreshInputSearchOverlay();
  });

  // ---------------------------------------------------------------
  // 3-2. 입력창 검색 (결과 패널과 동일하게 포함/일치/정규식 지원)
  // ---------------------------------------------------------------

  function escapeHtmlText(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /**
   * 입력 텍스트 전체를 대상으로 모드별 일치 구간 [start, end) 목록을 계산한다.
   * - contains: 대소문자 무시 부분 문자열
   * - exact: 줄 전체(앞뒤 공백 제외)가 검색어와 정확히 같은 줄만 강조
   * - regex: 정규식(gim) 전체 텍스트 매칭 — 잘못된 패턴이면 예외를 던진다
   */
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
        offset += line.length + 1; // split으로 사라진 "\n" 만큼 보정
      });
      return exactRanges;
    }

    if (mode === "regex") {
      var re = new RegExp(query, "gim"); // 잘못된 패턴이면 여기서 예외 발생 (호출부에서 처리)
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
    if (!ranges.length) return escapeHtmlText(text);
    var html = "";
    var cursor = 0;
    ranges.forEach(function (r, idx) {
      html += escapeHtmlText(text.slice(cursor, r[0]));
      var cls = "json-search-match" + (idx === activeIndex ? " is-active" : "");
      html += '<mark class="' + cls + '">' + escapeHtmlText(text.slice(r[0], r[1])) + "</mark>";
      cursor = r[1];
    });
    html += escapeHtmlText(text.slice(cursor));
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

  // 검색어/모드/텍스트를 기준으로 일치 구간을 다시 계산하고 오버레이를 새로 그린다.
  function computeAndRenderInputMatches() {
    var mode = els.inputSearchMode.value;
    var query = els.inputSearchInput.value;
    var text = els.input.value;

    var regexError = null;
    if (mode === "regex" && query) {
      try {
        // eslint-disable-next-line no-new
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
    updateInputSearchCount(regexError ? "정규식 오류" : null);
    updateInputSearchButtons();
  }

  // 텍스트 내용이 바뀔 때(타이핑, 정렬/예시/지우기 등) 호출 — 커서/선택 영역은 건드리지 않는다.
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
    var lineNumber = textBefore.split("\n").length; // 1-based
    var computed = window.getComputedStyle(textarea);
    var lineHeight = parseFloat(computed.lineHeight);
    if (!lineHeight || isNaN(lineHeight)) lineHeight = 21.8; // 0.88rem * 1.55 근사치
    var target = (lineNumber - 1) * lineHeight - textarea.clientHeight / 2 + lineHeight / 2;
    target = Math.max(0, Math.min(target, textarea.scrollHeight - textarea.clientHeight));
    textarea.scrollTop = target; // scroll 이벤트가 거터/오버레이 위치를 자동으로 동기화한다
  }

  // 검색 중에는 입력창(textarea)으로 포커스를 옮기지 않는다.
  // (과거에는 els.input.focus()를 호출했는데, 검색창에 연속으로 키를 입력하는 도중
  //  디바운스가 끝나며 포커스가 입력창으로 넘어가 버려서 이어지는 타이핑이 JSON 본문에
  //  들어가고 검증 로직이 오작동하는 문제가 있었다. 강조 표시는 오버레이(mark)로 충분하므로
  //  선택 영역만 갱신하고 스크롤만 이동시킨다.)
  function selectInputMatch(index, scrollIntoView) {
    var range = state.inputMatches[index];
    if (!range) return;
    if (document.activeElement === els.input) {
      // 사용자가 이미 입력창에 포커스를 두고 있을 때만 네이티브 선택 영역도 함께 보여준다.
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
        if (targetBtn && !targetBtn.disabled) {
          targetBtn.click();
        }
      }
    });

    els.inputSearchMode.addEventListener("change", function () {
      computeAndRenderInputMatches();
      if (state.inputActiveMatchIndex >= 0) {
        selectInputMatch(state.inputActiveMatchIndex, true);
      }
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

  function setToolbarEnabled(enabled) {
    [
      els.btnCopy,
      els.btnCopyMinify,
      els.btnDownload,
      els.btnExpandAll,
      els.btnCollapseAll,
      els.searchInput,
      els.searchMode,
      els.searchPrev,
      els.searchNext,
      els.searchClear,
    ].forEach(function (el) {
      if (el) el.disabled = !enabled;
    });
  }

  // ---------------------------------------------------------------
  // 4. 실행 파이프라인: 입력 -> 검증 -> 렌더링
  // ---------------------------------------------------------------

  function process() {
    var text = els.input.value;
    var parsed = tryParse(text);
    clearSearch();

    if (parsed.empty) {
      state.isValid = false;
      state.parsedValue = undefined;
      state.lastCorrectedLines = new Set();
      setStatus("idle", "JSON을 입력해주세요", "대기 중");
      renderPlaceholder();
      renderGutter(text, state.lastCorrectedLines);
      setToolbarEnabled(false);
      return;
    }

    if (!parsed.ok) {
      state.isValid = false;
      state.parsedValue = undefined;
      state.lastCorrectedLines = new Set();
      var detail = parsed.loc
        ? parsed.loc.line + "행 " + parsed.loc.column + "열 부근을 확인해주세요."
        : "구문을 확인해주세요.";
      setStatus("invalid", "유효하지 않은 JSON", "무효", detail);
      renderErrorBox(parsed, text);
      renderGutter(text, state.lastCorrectedLines);
      setToolbarEnabled(false);
      return;
    }

    state.isValid = true;
    state.parsedValue = parsed.value;
    if (parsed.mode === "lenient") {
      state.lastCorrectedLines = parsed.correctedLines || new Set();
      setStatus(
        "fixed",
        "보정됨 (따옴표 자동 인식)",
        "보정됨",
        "일부 키/값에 따옴표가 없어 자동으로 보정해서 인식했습니다. (입력창 줄 번호의 강조 표시 참고)"
      );
    } else {
      state.lastCorrectedLines = new Set();
      setStatus("valid", "유효한 JSON입니다", "유효함");
    }
    renderGutter(text, state.lastCorrectedLines);
    renderTree(parsed.value);
    setToolbarEnabled(true);
  }

  function scheduleProcess() {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(function () {
      process();
      // 키 입력 후 정상(유효 또는 보정됨) 상태가 되면 보기 편하도록 자동으로 결과 탭으로 전환
      if (state.isValid) {
        switchTab("output");
      }
    }, 250);
  }

  // ---------------------------------------------------------------
  // 5. 툴바 동작: 포맷/샘플/지우기/복사/다운로드
  // ---------------------------------------------------------------

  function getIndent() {
    var v = els.indentSelect.value;
    return v === "tab" ? "\t" : parseInt(v, 10);
  }

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
    if (state.isValid) {
      els.input.value = JSON.stringify(state.parsedValue, null, getIndent());
      process(); // 정렬 후에는 따옴표가 모두 채워지므로 줄 번호/보정 표시를 다시 갱신
    }
    refreshInputSearchOverlay();
  });

  els.btnSample.addEventListener("click", function () {
    els.input.value = SAMPLE_JSON;
    process();
    refreshInputSearchOverlay();
  });

  els.btnClear.addEventListener("click", function () {
    els.input.value = "";
    els.input.focus();
    process();
    refreshInputSearchOverlay();
  });

  els.btnCopy.addEventListener("click", function () {
    if (!state.isValid) return;
    copyToClipboard(JSON.stringify(state.parsedValue, null, getIndent()));
    flashButton(els.btnCopy, "복사됨 ✓");
  });

  els.btnCopyMinify.addEventListener("click", function () {
    if (!state.isValid) return;
    copyToClipboard(JSON.stringify(state.parsedValue));
    flashButton(els.btnCopyMinify, "복사됨 ✓");
  });

  els.btnDownload.addEventListener("click", function () {
    if (!state.isValid) return;
    var text = JSON.stringify(state.parsedValue, null, getIndent());
    var blob = new Blob([text], { type: "application/json" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "formatted.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  els.btnExpandAll.addEventListener("click", function () {
    setAllCollapsed(false);
  });
  els.btnCollapseAll.addEventListener("click", function () {
    setAllCollapsed(true);
  });

  function setAllCollapsed(collapsed) {
    var nodes = els.output.querySelectorAll(".json-node.is-collapsible");
    nodes.forEach(function (node) {
      node.classList.toggle("is-collapsed", collapsed);
      var toggle = toggleRegistry.get(node);
      if (toggle) {
        toggle.textContent = collapsed ? "▸" : "▾";
        toggle.setAttribute("aria-expanded", String(!collapsed));
      }
    });
    renderOutputGutter();
  }

  // ---------------------------------------------------------------
  // 6. 검색 (키/값 텍스트, 이전/다음 이동)
  // ---------------------------------------------------------------

  function clearSearch() {
    els.searchInput.value = "";
    els.searchInput.classList.remove("has-error");
    els.searchCount.classList.remove("has-error");
    state.matches = [];
    state.activeMatchIndex = -1;
    updateSearchCount();
  }

  function updateSearchCount(errorMessage) {
    if (errorMessage) {
      els.searchCount.textContent = errorMessage;
      els.searchCount.classList.add("has-error");
      return;
    }
    els.searchCount.classList.remove("has-error");
    if (state.matches.length === 0) {
      els.searchCount.textContent = "0 / 0";
    } else {
      els.searchCount.textContent = state.activeMatchIndex + 1 + " / " + state.matches.length;
    }
  }

  // 값이 큰따옴표로 감싸인 JSON 문자열이면(예: '"John"') 따옴표를 뺀 실제 값과
  // 그 오프셋(1)을 함께 돌려준다. "일치"/"정규식" 검색이 따옴표를 신경 쓰지 않고
  // 실제 값 기준으로 비교/매칭되도록 하기 위함이다.
  function unwrapQuotes(raw) {
    if (raw.length >= 2 && raw.charAt(0) === '"' && raw.charAt(raw.length - 1) === '"') {
      return { text: raw.slice(1, -1), offset: 1 };
    }
    return { text: raw, offset: 0 };
  }

  /**
   * raw(요소에 표시된 원본 텍스트) 안에서 검색 모드에 따라 하이라이트할
   * [start, end) 구간 목록을 계산한다. 정규식 오류는 그대로 throw 한다.
   */
  function computeMatchRanges(raw, mode, query) {
    if (!query) return [];

    if (mode === "contains") {
      var ranges = [];
      var lowerRaw = raw.toLowerCase();
      var q = query.toLowerCase();
      var idx = lowerRaw.indexOf(q);
      while (idx !== -1) {
        ranges.push([idx, idx + q.length]);
        idx = lowerRaw.indexOf(q, idx + q.length);
      }
      return ranges;
    }

    var unwrapped = unwrapQuotes(raw);

    if (mode === "exact") {
      var trimmedQuery = query.trim();
      if (trimmedQuery !== "" && unwrapped.text.toLowerCase() === trimmedQuery.toLowerCase()) {
        return [[unwrapped.offset, unwrapped.offset + unwrapped.text.length]];
      }
      return [];
    }

    if (mode === "regex") {
      var re = new RegExp(query, "gi"); // 잘못된 패턴이면 여기서 예외 발생 (호출부에서 처리)
      var regexRanges = [];
      var m;
      while ((m = re.exec(unwrapped.text)) !== null) {
        if (m[0].length === 0) {
          re.lastIndex++;
          continue;
        }
        regexRanges.push([unwrapped.offset + m.index, unwrapped.offset + m.index + m[0].length]);
      }
      return regexRanges;
    }

    return [];
  }

  function buildHighlightedHtml(raw, ranges) {
    if (!ranges.length) return null;
    var html = "";
    var cursor = 0;
    ranges.forEach(function (r) {
      html += escapeHtml(raw.slice(cursor, r[0]));
      html += '<mark class="json-search-match">' + escapeHtml(raw.slice(r[0], r[1])) + "</mark>";
      cursor = r[1];
    });
    html += escapeHtml(raw.slice(cursor));
    return html;
  }

  function runSearch(query) {
    var searchables = els.output.querySelectorAll(".json-key, .json-value");
    var mode = els.searchMode ? els.searchMode.value : "contains";

    var regexError = null;
    if (mode === "regex" && query) {
      try {
        // eslint-disable-next-line no-new
        new RegExp(query, "gi");
      } catch (e) {
        regexError = e;
      }
    }
    els.searchInput.classList.toggle("has-error", !!regexError);

    searchables.forEach(function (el) {
      var raw = el.dataset.raw;
      if (raw === undefined) return;
      if (!query || regexError) {
        el.textContent = raw;
        return;
      }
      var ranges;
      try {
        ranges = computeMatchRanges(raw, mode, query);
      } catch (e) {
        ranges = [];
      }
      var html = buildHighlightedHtml(raw, ranges);
      if (html) {
        el.innerHTML = html;
      } else {
        el.textContent = raw;
      }
    });

    state.matches = Array.prototype.slice.call(els.output.querySelectorAll(".json-search-match"));
    state.activeMatchIndex = state.matches.length > 0 ? 0 : -1;
    focusActiveMatch(true);
    updateSearchCount(regexError ? "정규식 오류" : null);
  }

  function expandAncestors(el) {
    var node = el.closest(".json-node");
    while (node) {
      if (node.classList.contains("is-collapsed")) {
        node.classList.remove("is-collapsed");
        var toggle = toggleRegistry.get(node);
        if (toggle) {
          toggle.textContent = "▾";
          toggle.setAttribute("aria-expanded", "true");
        }
      }
      var parent = node.parentElement ? node.parentElement.closest(".json-node") : null;
      node = parent;
    }
  }

  function focusActiveMatch(scroll) {
    state.matches.forEach(function (m) {
      m.classList.remove("is-active");
    });
    if (state.activeMatchIndex < 0 || !state.matches[state.activeMatchIndex]) return;
    var active = state.matches[state.activeMatchIndex];
    expandAncestors(active);
    renderOutputGutter();
    active.classList.add("is-active");
    if (scroll) {
      active.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }

  function goToMatch(delta) {
    if (state.matches.length === 0) return;
    state.activeMatchIndex = (state.activeMatchIndex + delta + state.matches.length) % state.matches.length;
    focusActiveMatch(true);
    updateSearchCount();
  }

  var searchDebounce = null;
  els.searchInput.addEventListener("input", function () {
    clearTimeout(searchDebounce);
    var value = els.searchInput.value;
    searchDebounce = setTimeout(function () {
      runSearch(value);
    }, 150);
  });

  els.searchInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      var targetBtn = e.shiftKey ? els.searchPrev : els.searchNext;
      if (targetBtn && !targetBtn.disabled) {
        targetBtn.click();
      }
    }
  });

  if (els.searchMode) {
    els.searchMode.addEventListener("change", function () {
      runSearch(els.searchInput.value);
    });
  }

  els.searchNext.addEventListener("click", function () {
    goToMatch(1);
  });
  els.searchPrev.addEventListener("click", function () {
    goToMatch(-1);
  });
  els.searchClear.addEventListener("click", function () {
    clearSearch();
    runSearch("");
    els.searchInput.focus();
  });

  // ---------------------------------------------------------------
  // 7. 탭 전환 (입력 / 결과)
  // ---------------------------------------------------------------

  function switchTab(tab) {
    var showInput = tab === "input";
    els.tabInput.classList.toggle("is-active", showInput);
    els.tabOutput.classList.toggle("is-active", !showInput);
    els.tabInput.setAttribute("aria-selected", String(showInput));
    els.tabOutput.setAttribute("aria-selected", String(!showInput));
    els.panelInput.hidden = !showInput;
    els.panelOutput.hidden = showInput;
    if (!showInput && !els.searchInput.disabled) {
      // 결과 탭이 보이면 바로 타이핑할 수 있도록 검색창에 포커스
      els.searchInput.focus();
    }
  }

  els.tabInput.addEventListener("click", function () {
    switchTab("input");
  });
  els.tabOutput.addEventListener("click", function () {
    switchTab("output");
  });

  // ---------------------------------------------------------------
  // 8. 초기화
  // ---------------------------------------------------------------

  els.input.value = SAMPLE_JSON;
  setToolbarEnabled(false);
  process();
  refreshInputSearchOverlay();
})();
