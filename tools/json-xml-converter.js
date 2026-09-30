/**
 * JSON ↔ XML 변환기
 * - 입력이 JSON인지 XML인지 첫 글자로 자동 감지하거나, 사용자가 방향을 직접 선택할 수 있음
 * - JSON → XML: 최상위 배열은 <root><item>...</item></root>, 최상위 객체는 <root>의 자식 엘리먼트로 변환
 *   객체 안의 배열 값은 같은 태그명을 가진 형제 엘리먼트 여러 개로 변환(배열 래퍼 없음)
 * - XML → JSON: 엘리먼트 속성은 "@attributes" 객체로, 같은 이름의 형제 엘리먼트는 배열로 변환
 * - 이 변환은 손실 없는 완전한 왕복(JSON→XML→JSON)을 보장하지 않는, 문서화된 고정 규칙을 따름
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
      statusIdleText: "Paste some JSON or XML", statusIdleTop: "Idle",
      statusInvalidJsonText: "Invalid JSON", statusInvalidXmlText: "Invalid XML", statusInvalidTop: "Invalid",
      statusValidText: "Converted", statusValidTop: "Done",
      detailInvalid: function (line, col) { return "Check around line " + line + ", column " + col + "."; },
      detailInvalidGeneric: "Please check the syntax.",
      outputPlaceholder: "Paste JSON or XML on the left to see the converted result here.",
      errorBoxTitleJson: "The JSON format is invalid.",
      errorBoxTitleXml: "The XML format is invalid.",
      errorLocation: function (line, col) { return "Error location: around line " + line + ", character " + col; },
      unknownError: "Unknown error", regexError: "Regex error", copied: "Copied ✓",
    },
    ko: {
      statusIdleText: "JSON 또는 XML을 붙여넣어주세요", statusIdleTop: "대기 중",
      statusInvalidJsonText: "유효하지 않은 JSON", statusInvalidXmlText: "유효하지 않은 XML", statusInvalidTop: "무효",
      statusValidText: "변환 완료", statusValidTop: "완료",
      detailInvalid: function (line, col) { return line + "행 " + col + "열 부근을 확인해주세요."; },
      detailInvalidGeneric: "구문을 확인해주세요.",
      outputPlaceholder: "왼쪽에 JSON 또는 XML을 붙여넣으면 변환 결과가 여기에 표시됩니다.",
      errorBoxTitleJson: "JSON 형식이 올바르지 않습니다.",
      errorBoxTitleXml: "XML 형식이 올바르지 않습니다.",
      errorLocation: function (line, col) { return "오류 위치: " + line + "번째 줄, " + col + "번째 문자 부근"; },
      unknownError: "알 수 없는 오류", regexError: "정규식 오류", copied: "복사됨 ✓",
    },
    ja: {
      statusIdleText: "JSONまたはXMLを貼り付けてください", statusIdleTop: "待機中",
      statusInvalidJsonText: "無効なJSON", statusInvalidXmlText: "無効なXML", statusInvalidTop: "無効",
      statusValidText: "変換完了", statusValidTop: "完了",
      detailInvalid: function (line, col) { return line + "行目" + col + "列目付近をご確認ください。"; },
      detailInvalidGeneric: "構文をご確認ください。",
      outputPlaceholder: "左側にJSONまたはXMLを貼り付けると、変換結果がここに表示されます。",
      errorBoxTitleJson: "JSON形式が正しくありません。",
      errorBoxTitleXml: "XML形式が正しくありません。",
      errorLocation: function (line, col) { return "エラー位置: " + line + "行目、" + col + "文字目付近"; },
      unknownError: "不明なエラー", regexError: "正規表現エラー", copied: "コピーしました ✓",
    },
    zh: {
      statusIdleText: "请粘贴 JSON 或 XML", statusIdleTop: "待处理",
      statusInvalidJsonText: "无效的 JSON", statusInvalidXmlText: "无效的 XML", statusInvalidTop: "无效",
      statusValidText: "转换完成", statusValidTop: "完成",
      detailInvalid: function (line, col) { return "请检查第 " + line + " 行第 " + col + " 列附近。"; },
      detailInvalidGeneric: "请检查语法。",
      outputPlaceholder: "在左侧粘贴 JSON 或 XML，转换结果将显示在这里。",
      errorBoxTitleJson: "JSON 格式无效。",
      errorBoxTitleXml: "XML 格式无效。",
      errorLocation: function (line, col) { return "错误位置：第 " + line + " 行，第 " + col + " 个字符附近"; },
      unknownError: "未知错误", regexError: "正则表达式错误", copied: "已复制 ✓",
    },
  };
  var T = MESSAGES[LANG];

  var els = {
    input: document.getElementById("conv-input"),
    status: document.getElementById("conv-status"),
    statusTop: document.getElementById("conv-status-top"),
    errorDetail: document.getElementById("conv-error-detail"),
    errorDetailTop: document.getElementById("conv-error-detail-top"),
    output: document.getElementById("conv-output"),
    gutter: document.getElementById("conv-gutter"),
    gutterInner: document.getElementById("conv-gutter-inner"),
    inputHighlight: document.getElementById("conv-input-highlight"),
    inputSearchMode: document.getElementById("conv-input-search-mode"),
    inputSearchInput: document.getElementById("conv-input-search"),
    inputSearchCount: document.getElementById("conv-input-search-count"),
    inputSearchPrev: document.getElementById("btn-input-search-prev"),
    inputSearchNext: document.getElementById("btn-input-search-next"),
    inputSearchClear: document.getElementById("btn-input-search-clear"),
    outputGutter: document.getElementById("conv-output-gutter"),
    outputGutterInner: document.getElementById("conv-output-gutter-inner"),
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
    directionSelect: document.getElementById("conv-direction-select"),
    searchInput: document.getElementById("conv-search"),
    searchMode: document.getElementById("conv-search-mode"),
    searchPrev: document.getElementById("btn-search-prev"),
    searchNext: document.getElementById("btn-search-next"),
    searchClear: document.getElementById("btn-search-clear"),
  };

  if (!els.input) return; // 이 페이지가 아니면 아무 것도 하지 않음

  var state = {
    outputText: "",
    outputKind: "", // "xml" | "json"
    isValid: false,
    debounceTimer: null,
    inputMatches: [],
    inputActiveMatchIndex: -1,
  };

  var SAMPLE_JSON = JSON.stringify(
    {
      id: 1024,
      name: "JSON Formatter",
      maker: "Formix",
      isFree: true,
      rating: 4.8,
      tags: ["json", "formatter", "viewer"],
      pricing: { amount: 0, currency: "USD" },
      screenshots: [],
      relatedTools: [
        { id: "xml-formatter", name: "XML Formatter" },
        { id: "sql-formatter", name: "SQL Formatter" },
        { id: "code-viewer", name: "Code Viewer" },
      ],
      deprecatedSince: null,
    },
    null,
    2
  );

  // ---------------------------------------------------------------
  // 1. 형식 자동 감지
  // ---------------------------------------------------------------

  function detectFormat(text) {
    var trimmed = text.replace(/^\s+/, "");
    var ch = trimmed.charAt(0);
    if (ch === "<") return "xml";
    if (ch === "{" || ch === "[") return "json";
    return null;
  }

  function resolveDirection(text) {
    var dir = els.directionSelect ? els.directionSelect.value : "auto";
    if (dir === "json2xml") return "json2xml";
    if (dir === "xml2json") return "xml2json";
    var detected = detectFormat(text);
    if (detected === "xml") return "xml2json";
    return "json2xml"; // json이거나 애매하면 기본적으로 json -> xml 시도
  }

  // ---------------------------------------------------------------
  // 2. JSON → XML 변환
  // ---------------------------------------------------------------

  function escapeXmlText(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function escapeXmlAttr(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }

  /** JSON 객체 키를 XML 태그명으로 사용할 수 있도록 정리한다. */
  function sanitizeTagName(name) {
    var cleaned = String(name).replace(/[^A-Za-z0-9_.-]/g, "_");
    if (!cleaned || /^[0-9.\-]/.test(cleaned)) cleaned = "_" + cleaned;
    return cleaned || "_";
  }

  function primitiveToXmlText(value) {
    if (value === true) return "true";
    if (value === false) return "false";
    return escapeXmlText(String(value));
  }

  /** value를 tagName 엘리먼트 하나로 직렬화한다(값이 배열이면 이 함수를 호출하기 전에 형제 엘리먼트로 나눠야 함). */
  function renderElement(tagName, value, indent, level) {
    var tag = sanitizeTagName(tagName);
    var pad = indent ? indent.repeat(level) : "";
    var nl = indent ? "\n" : "";

    if (value === null || value === undefined) {
      return pad + "<" + tag + " />" + nl;
    }
    if (Array.isArray(value)) {
      // 배열 값이 다시 배열/객체를 직접 감쌀 위치에 온 경우(예: 배열의 배열):
      // 키가 없으므로 "item"이라는 이름으로 형제 엘리먼트를 만들어 구조를 보존한다.
      if (value.length === 0) return pad + "<" + tag + " />" + nl;
      var inner = "";
      value.forEach(function (item) {
        inner += renderElement("item", item, indent, level + 1);
      });
      return pad + "<" + tag + ">" + nl + inner + pad + "</" + tag + ">" + nl;
    }
    if (typeof value === "object") {
      var keys = Object.keys(value);
      if (keys.length === 0) return pad + "<" + tag + " />" + nl;
      var body = "";
      keys.forEach(function (key) {
        var v = value[key];
        if (Array.isArray(v)) {
          v.forEach(function (item) {
            body += renderElement(key, item, indent, level + 1);
          });
        } else {
          body += renderElement(key, v, indent, level + 1);
        }
      });
      return pad + "<" + tag + ">" + nl + body + pad + "</" + tag + ">" + nl;
    }
    // 원시값(문자열/숫자/불리언)
    var text = primitiveToXmlText(value);
    if (text === "") return pad + "<" + tag + " />" + nl;
    return pad + "<" + tag + ">" + text + "</" + tag + ">" + nl;
  }

  function jsonToXml(rootValue, indentStr) {
    var pretty = indentStr !== "";
    var declaration = '<?xml version="1.0" encoding="UTF-8"?>' + (pretty ? "\n" : "");
    return declaration + renderElement("root", rootValue, indentStr, 0).replace(/\n$/, "");
  }

  // ---------------------------------------------------------------
  // 3. XML → JSON 변환
  // ---------------------------------------------------------------

  function locateXmlErrorPosition(errorText) {
    var m = /error on line (\d+) at column (\d+)/i.exec(errorText || "");
    if (m) return { line: parseInt(m[1], 10), column: parseInt(m[2], 10) };
    m = /line number (\d+),\s*column (\d+)/i.exec(errorText || "");
    if (m) return { line: parseInt(m[1], 10), column: parseInt(m[2], 10) };
    m = /line[:\s]+(\d+)[^\d]+column[:\s]+(\d+)/i.exec(errorText || "");
    if (m) return { line: parseInt(m[1], 10), column: parseInt(m[2], 10) };
    return null;
  }

  function inferPrimitive(text) {
    if (text === "true") return true;
    if (text === "false") return false;
    if (text === "null") return null;
    if (text !== "" && /^-?\d+(\.\d+)?$/.test(text)) {
      var n = Number(text);
      if (!isNaN(n)) return n;
    }
    return text;
  }

  /** DOM 엘리먼트를 JSON 값으로 변환한다. */
  function domElementToJson(el) {
    var attrs = {};
    var hasAttrs = false;
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i];
      attrs[a.name] = a.value;
      hasAttrs = true;
    }

    var childElements = [];
    var textParts = [];
    for (var j = 0; j < el.childNodes.length; j++) {
      var node = el.childNodes[j];
      if (node.nodeType === 1) childElements.push(node);
      else if (node.nodeType === 3 || node.nodeType === 4) textParts.push(node.nodeValue);
    }
    var text = textParts.join("").trim();

    if (childElements.length === 0) {
      if (!hasAttrs) {
        return text === "" ? null : inferPrimitive(text);
      }
      var leafObj = { "@attributes": attrs };
      if (text !== "") leafObj["#text"] = inferPrimitive(text);
      return leafObj;
    }

    var obj = {};
    if (hasAttrs) obj["@attributes"] = attrs;
    childElements.forEach(function (child) {
      var key = child.nodeName;
      var value = domElementToJson(child);
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        if (!Array.isArray(obj[key])) obj[key] = [obj[key]];
        obj[key].push(value);
      } else {
        obj[key] = value;
      }
    });
    return obj;
  }

  function tryParseXml(text) {
    if (text.trim() === "") return { ok: false, empty: true };
    var parser = new DOMParser();
    var doc = parser.parseFromString(text, "application/xml");
    var errorNode = doc.querySelector("parsererror");
    if (errorNode) {
      var msg = errorNode.textContent || T.unknownError;
      return { ok: false, message: msg.split("\n").slice(0, 3).join(" ").trim(), loc: locateXmlErrorPosition(msg) };
    }
    if (!doc.documentElement) return { ok: false, message: T.unknownError, loc: null };
    var result = {};
    result[doc.documentElement.nodeName] = domElementToJson(doc.documentElement);
    return { ok: true, value: result };
  }

  // ---------------------------------------------------------------
  // 4. JSON 파싱 (오류 위치 안내용)
  // ---------------------------------------------------------------

  function locateJsonErrorPosition(text, message) {
    var match = /position (\d+)/.exec(message || "");
    if (!match) return null;
    var pos = parseInt(match[1], 10);
    var upTo = text.slice(0, pos);
    var lines = upTo.split("\n");
    return { pos: pos, line: lines.length, column: lines[lines.length - 1].length + 1 };
  }

  function tryParseJson(text) {
    if (text.trim() === "") return { ok: false, empty: true };
    try {
      return { ok: true, value: JSON.parse(text) };
    } catch (e) {
      return { ok: false, message: e.message, loc: locateJsonErrorPosition(text, e.message) };
    }
  }

  // ---------------------------------------------------------------
  // 5. 들여쓰기 / 출력 렌더링
  // ---------------------------------------------------------------

  function getIndentStr() {
    var v = els.indentSelect.value;
    return v === "tab" ? "\t" : " ".repeat(parseInt(v, 10));
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ---------------------------------------------------------------
  // 5-1. 출력 문법 강조 (JSON 포매터 / XML 포매터와 같은 색상 규칙 재사용)
  // ---------------------------------------------------------------

  function highlightJsonText(text) {
    // 문자열 뒤에 ":"가 바로(공백 허용) 이어지면 키, 아니면 값(문자열)으로 취급한다.
    // 캡처 그룹으로 문자열 부분과 뒤따르는 구분자(공백+:)를 분리해 문자열에만 색을 칠한다.
    var re = /("(?:\\.|[^"\\])*")([ \t]*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|[{}\[\],:]/g;
    var html = "";
    var cursor = 0;
    var m;
    while ((m = re.exec(text)) !== null) {
      html += escapeHtml(text.slice(cursor, m.index));
      var tok = m[0];
      if (m[1] !== undefined) {
        var isKey = m[2] !== undefined;
        html += '<span class="' + (isKey ? "json-key" : "json-string") + '">' + escapeHtml(m[1]) + "</span>";
        if (isKey) html += escapeHtml(m[2]);
      } else if (tok === "true" || tok === "false") {
        html += '<span class="json-boolean">' + tok + "</span>";
      } else if (tok === "null") {
        html += '<span class="json-null">' + tok + "</span>";
      } else if (/^[{}\[\],:]$/.test(tok)) {
        html += '<span class="json-punct">' + tok + "</span>";
      } else {
        html += '<span class="json-number">' + tok + "</span>";
      }
      cursor = m.index + tok.length;
    }
    html += escapeHtml(text.slice(cursor));
    return html;
  }

  function renderXmlTag(tag) {
    if (/^<\?/.test(tag)) {
      return '<span class="xml-decl">' + escapeHtml(tag) + "</span>";
    }
    var m = /^<(\/)?([^\s/>]+)(\s*\/)?>$/.exec(tag);
    if (!m) return escapeHtml(tag);
    var closing = !!m[1];
    var tagName = m[2];
    var selfClose = !!m[3];
    var html = '<span class="xml-bracket">' + (closing ? "&lt;/" : "&lt;") + "</span>";
    html += '<span class="xml-tag">' + escapeHtml(tagName) + "</span>";
    html += '<span class="xml-bracket">' + (selfClose ? " /&gt;" : "&gt;") + "</span>";
    return html;
  }

  function highlightXmlText(text) {
    var html = "";
    var cursor = 0;
    var re = /<[^>]*>/g;
    var m;
    while ((m = re.exec(text)) !== null) {
      var textRun = text.slice(cursor, m.index);
      html += textRun.trim() === "" ? escapeHtml(textRun) : '<span class="xml-text">' + escapeHtml(textRun) + "</span>";
      html += renderXmlTag(m[0]);
      cursor = m.index + m[0].length;
    }
    var tailRun = text.slice(cursor);
    html += tailRun.trim() === "" ? escapeHtml(tailRun) : '<span class="xml-text">' + escapeHtml(tailRun) + "</span>";
    return html;
  }

  function renderOutputText(text, kind) {
    els.output.innerHTML = '<pre class="conv-output-text"></pre>';
    if (kind === "json") {
      els.output.firstChild.innerHTML = highlightJsonText(text);
    } else if (kind === "xml") {
      els.output.firstChild.innerHTML = highlightXmlText(text);
    } else {
      els.output.firstChild.textContent = text;
    }
    renderOutputGutter(text);
  }

  function renderPlaceholder() {
    els.output.innerHTML = '<p class="jf-placeholder">' + escapeHtml(T.outputPlaceholder) + "</p>";
    renderOutputGutter("");
  }

  function renderErrorBox(title, parsed) {
    var lines = [];
    lines.push("<p><strong>" + escapeHtml(title) + "</strong></p>");
    if (parsed.loc) {
      lines.push("<p>" + escapeHtml(T.errorLocation(parsed.loc.line, parsed.loc.column)) + "</p>");
    }
    lines.push("<p><code>" + escapeHtml(parsed.message || T.unknownError) + "</code></p>");
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

  // ---------------------------------------------------------------
  // 6. 상태 표시
  // ---------------------------------------------------------------

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

  // ---------------------------------------------------------------
  // 7. 입력창 줄 번호
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
  // 8. 입력창 검색
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

  function setToolbarEnabled(enabled) {
    [els.btnCopy, els.btnCopyMinify, els.btnDownload].forEach(function (el) {
      if (el) el.disabled = !enabled;
    });
  }

  // ---------------------------------------------------------------
  // 9. 실행 파이프라인
  // ---------------------------------------------------------------

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

    var direction = resolveDirection(text);
    var indentStr = getIndentStr();

    if (direction === "json2xml") {
      var parsedJson = tryParseJson(text);
      if (!parsedJson.ok) {
        state.isValid = false;
        state.outputText = "";
        var detailJ = parsedJson.loc ? T.detailInvalid(parsedJson.loc.line, parsedJson.loc.column) : T.detailInvalidGeneric;
        setStatus("invalid", T.statusInvalidJsonText, T.statusInvalidTop, detailJ);
        renderErrorBox(T.errorBoxTitleJson, parsedJson);
        renderGutter(text);
        setToolbarEnabled(false);
        return;
      }
      state.isValid = true;
      state.outputKind = "xml";
      state.outputText = jsonToXml(parsedJson.value, indentStr);
      setStatus("valid", T.statusValidText, T.statusValidTop);
      renderGutter(text);
      renderOutputText(state.outputText, state.outputKind);
      setToolbarEnabled(true);
      return;
    }

    // xml2json
    var parsedXml = tryParseXml(text);
    if (!parsedXml.ok) {
      state.isValid = false;
      state.outputText = "";
      var detailX = parsedXml.loc ? T.detailInvalid(parsedXml.loc.line, parsedXml.loc.column) : T.detailInvalidGeneric;
      setStatus("invalid", T.statusInvalidXmlText, T.statusInvalidTop, detailX);
      renderErrorBox(T.errorBoxTitleXml, parsedXml);
      renderGutter(text);
      setToolbarEnabled(false);
      return;
    }
    state.isValid = true;
    state.outputKind = "json";
    state.outputText = JSON.stringify(parsedXml.value, null, indentStr);
    setStatus("valid", T.statusValidText, T.statusValidTop);
    renderGutter(text);
    renderOutputText(state.outputText, state.outputKind);
    setToolbarEnabled(true);
  }

  function scheduleProcess() {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(function () {
      process();
      if (state.isValid) switchTab("output");
    }, 250);
  }

  // ---------------------------------------------------------------
  // 10. 툴바 동작
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
    els.input.value = SAMPLE_JSON;
    if (els.directionSelect) els.directionSelect.value = "auto";
    process();
    refreshInputSearchOverlay();
  });

  els.btnClear.addEventListener("click", function () {
    els.input.value = "";
    els.input.focus();
    process();
    refreshInputSearchOverlay();
  });

  if (els.directionSelect) {
    els.directionSelect.addEventListener("change", function () {
      process();
    });
  }

  els.btnCopy.addEventListener("click", function () {
    if (!state.isValid) return;
    copyToClipboard(state.outputText);
    flashButton(els.btnCopy, T.copied);
  });

  els.btnCopyMinify.addEventListener("click", function () {
    if (!state.isValid) return;
    var minified =
      state.outputKind === "xml"
        ? jsonToXml(tryParseJson(els.input.value).ok ? tryParseJson(els.input.value).value : null, "")
        : (function () {
            var parsed = tryParseXml(els.input.value);
            return parsed.ok ? JSON.stringify(parsed.value) : state.outputText;
          })();
    copyToClipboard(minified);
    flashButton(els.btnCopyMinify, T.copied);
  });

  els.btnDownload.addEventListener("click", function () {
    if (!state.isValid) return;
    var ext = state.outputKind === "xml" ? "xml" : "json";
    var mime = state.outputKind === "xml" ? "application/xml" : "application/json";
    var blob = new Blob([state.outputText], { type: mime });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "converted." + ext;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // ---------------------------------------------------------------
  // 11. 탭 전환
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
  // 12. 초기화
  // ---------------------------------------------------------------

  els.input.value = SAMPLE_JSON;
  setToolbarEnabled(false);
  process();
  refreshInputSearchOverlay();
})();
