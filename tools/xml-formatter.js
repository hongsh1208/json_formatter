/**
 * XML 포매터 / 뷰어
 * - 입력한 문자열이 유효한 XML인지 검사 (브라우저 내장 DOMParser 사용)
 * - 들여쓰기 + 문법 강조가 적용된 트리 형태로 렌더링 (태그/속성/텍스트/주석/CDATA)
 * - 노드별 접기/펼치기, 전체 펼치기/접기
 * - 태그명/속성/텍스트 검색 (이전/다음 이동, 일치 개수 표시)
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
      statusIdleText: "Enter some XML", statusIdleTop: "Idle",
      statusInvalidText: "Invalid XML", statusInvalidTop: "Invalid",
      statusValidText: "Valid XML", statusValidTop: "Valid",
      detailInvalid: function (line, col) { return "Check around line " + line + ", column " + col + "."; },
      detailInvalidGeneric: "Please check the syntax.",
      toggleAria: "Collapse/expand node",
      outputPlaceholder: "Enter an XML string on the left to see the result here.",
      errorBoxTitle: "The XML format is invalid.",
      errorLocation: function (line, col) { return "Error location: around line " + line + ", character " + col; },
      unknownError: "Unknown error", regexError: "Regex error", copied: "Copied ✓",
      previewSuffix: function (n) { return n + " nodes"; },
      emptyElement: "(empty)",
    },
    ko: {
      statusIdleText: "XML을 입력해주세요", statusIdleTop: "대기 중",
      statusInvalidText: "유효하지 않은 XML", statusInvalidTop: "무효",
      statusValidText: "유효한 XML입니다", statusValidTop: "유효함",
      detailInvalid: function (line, col) { return line + "행 " + col + "열 부근을 확인해주세요."; },
      detailInvalidGeneric: "구문을 확인해주세요.",
      toggleAria: "노드 접기/펼치기",
      outputPlaceholder: "왼쪽에 XML 문자열을 입력하면 결과가 여기에 표시됩니다.",
      errorBoxTitle: "XML 형식이 올바르지 않습니다.",
      errorLocation: function (line, col) { return "오류 위치: " + line + "번째 줄, " + col + "번째 문자 부근"; },
      unknownError: "알 수 없는 오류", regexError: "정규식 오류", copied: "복사됨 ✓",
      previewSuffix: function (n) { return n + "개 노드"; },
      emptyElement: "(비어 있음)",
    },
    ja: {
      statusIdleText: "XMLを入力してください", statusIdleTop: "待機中",
      statusInvalidText: "無効なXML", statusInvalidTop: "無効",
      statusValidText: "有効なXMLです", statusValidTop: "有効",
      detailInvalid: function (line, col) { return line + "行目" + col + "列目付近をご確認ください。"; },
      detailInvalidGeneric: "構文をご確認ください。",
      toggleAria: "ノードの折りたたみ/展開",
      outputPlaceholder: "左側にXML文字列を入力すると、ここに結果が表示されます。",
      errorBoxTitle: "XML形式が正しくありません。",
      errorLocation: function (line, col) { return "エラー位置: " + line + "行目、" + col + "文字目付近"; },
      unknownError: "不明なエラー", regexError: "正規表現エラー", copied: "コピーしました ✓",
      previewSuffix: function (n) { return n + "個のノード"; },
      emptyElement: "(空)",
    },
    zh: {
      statusIdleText: "请输入 XML", statusIdleTop: "待处理",
      statusInvalidText: "无效的 XML", statusInvalidTop: "无效",
      statusValidText: "有效的 XML", statusValidTop: "有效",
      detailInvalid: function (line, col) { return "请检查第 " + line + " 行第 " + col + " 列附近。"; },
      detailInvalidGeneric: "请检查语法。",
      toggleAria: "折叠/展开节点",
      outputPlaceholder: "在左侧输入 XML 字符串，结果将显示在这里。",
      errorBoxTitle: "XML 格式无效。",
      errorLocation: function (line, col) { return "错误位置：第 " + line + " 行，第 " + col + " 个字符附近"; },
      unknownError: "未知错误", regexError: "正则表达式错误", copied: "已复制 ✓",
      previewSuffix: function (n) { return n + " 个节点"; },
      emptyElement: "(空)",
    },
  };
  var T = MESSAGES[LANG];

  var els = {
    input: document.getElementById("xml-input"),
    status: document.getElementById("xml-status"),
    statusTop: document.getElementById("xml-status-top"),
    errorDetail: document.getElementById("xml-error-detail"),
    errorDetailTop: document.getElementById("xml-error-detail-top"),
    output: document.getElementById("xml-output"),
    gutter: document.getElementById("xml-gutter"),
    gutterInner: document.getElementById("xml-gutter-inner"),
    inputHighlight: document.getElementById("xml-input-highlight"),
    inputSearchMode: document.getElementById("xml-input-search-mode"),
    inputSearchInput: document.getElementById("xml-input-search"),
    inputSearchCount: document.getElementById("xml-input-search-count"),
    inputSearchPrev: document.getElementById("btn-input-search-prev"),
    inputSearchNext: document.getElementById("btn-input-search-next"),
    inputSearchClear: document.getElementById("btn-input-search-clear"),
    outputGutter: document.getElementById("xml-output-gutter"),
    outputGutterInner: document.getElementById("xml-output-gutter-inner"),
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
    searchInput: document.getElementById("xml-search"),
    searchMode: document.getElementById("xml-search-mode"),
    searchCount: document.getElementById("jf-search-count"),
    searchPrev: document.getElementById("btn-search-prev"),
    searchNext: document.getElementById("btn-search-next"),
    searchClear: document.getElementById("btn-search-clear"),
  };

  if (!els.input) return; // 이 페이지가 아니면 아무 것도 하지 않음

  var state = {
    parsedTree: undefined,
    declaration: "",
    isValid: false,
    debounceTimer: null,
    matches: [],
    activeMatchIndex: -1,
    inputMatches: [],
    inputActiveMatchIndex: -1,
  };

  var toggleRegistry = new Map();

  var SAMPLE_XML =
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
    '<toolbox version="2.4.1" updated="2026-09-30">\n' +
    "  <!-- Formix official tool catalog -->\n" +
    '  <tool id="json-formatter" available="true">\n' +
    "    <name>JSON Formatter</name>\n" +
    "    <maker>Formix</maker>\n" +
    "    <category>Data</category>\n" +
    '    <price currency="USD">0.00</price>\n' +
    "    <description><![CDATA[Validate and beautify JSON right in your browser.]]></description>\n" +
    "    <tags>\n" +
    "      <tag>json</tag>\n" +
    "      <tag>formatter</tag>\n" +
    "      <tag>viewer</tag>\n" +
    "    </tags>\n" +
    "  </tool>\n" +
    '  <tool id="xml-formatter" available="true">\n' +
    "    <name>XML Formatter</name>\n" +
    "    <maker>Formix</maker>\n" +
    "    <category>Data</category>\n" +
    '    <price currency="USD">0.00</price>\n' +
    "    <description><![CDATA[Validate and beautify XML with a collapsible tree view.]]></description>\n" +
    "    <tags>\n" +
    "      <tag>xml</tag>\n" +
    "      <tag>formatter</tag>\n" +
    "    </tags>\n" +
    "  </tool>\n" +
    '  <tool id="sql-formatter" available="true">\n' +
    "    <name>SQL Formatter</name>\n" +
    "    <maker>Formix</maker>\n" +
    "    <category>Database</category>\n" +
    '    <price currency="USD">0.00</price>\n' +
    "    <description><![CDATA[Beautify SQL queries across multiple dialects.]]></description>\n" +
    "  </tool>\n" +
    '  <tool id="code-viewer" available="true">\n' +
    "    <name>Code Viewer</name>\n" +
    "    <maker>Formix</maker>\n" +
    "    <category>Developer</category>\n" +
    '    <price currency="USD">0.00</price>\n' +
    "    <description><![CDATA[Syntax highlighting for 20+ programming languages.]]></description>\n" +
    "  </tool>\n" +
    '  <tool id="csv-converter" available="false">\n' +
    "    <name>CSV Converter</name>\n" +
    "    <maker>Formix</maker>\n" +
    "    <category>Data</category>\n" +
    "    <!-- Coming soon -->\n" +
    "  </tool>\n" +
    "</toolbox>";

  // ---------------------------------------------------------------
  // 1. 파싱 / 유효성 검사 (DOMParser 기반)
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

  /** DOM 노드(엘리먼트/텍스트/주석/CDATA)를 렌더링용 단순 트리로 변환한다. */
  function convertNode(domNode) {
    if (domNode.nodeType === 1) {
      // ELEMENT_NODE
      var attrs = [];
      for (var i = 0; i < domNode.attributes.length; i++) {
        var a = domNode.attributes[i];
        attrs.push([a.name, a.value]);
      }
      var children = [];
      for (var j = 0; j < domNode.childNodes.length; j++) {
        var child = domNode.childNodes[j];
        if (child.nodeType === 3 && child.nodeValue.trim() === "") continue; // whitespace-only text
        if (child.nodeType === 8 || child.nodeType === 3 || child.nodeType === 4 || child.nodeType === 1) {
          children.push(convertNode(child));
        }
      }
      return { type: "element", tag: domNode.nodeName, attrs: attrs, children: children };
    }
    if (domNode.nodeType === 3) return { type: "text", text: domNode.nodeValue };
    if (domNode.nodeType === 4) return { type: "cdata", text: domNode.nodeValue };
    if (domNode.nodeType === 8) return { type: "comment", text: domNode.nodeValue };
    return { type: "text", text: "" };
  }

  function tryParse(text) {
    if (text.trim() === "") return { ok: false, empty: true };
    var parser = new DOMParser();
    var doc = parser.parseFromString(text, "application/xml");
    var errorNode = doc.querySelector("parsererror");
    if (errorNode) {
      var msg = errorNode.textContent || T.unknownError;
      return { ok: false, message: msg.split("\n").slice(0, 3).join(" ").trim(), loc: locateXmlErrorPosition(msg) };
    }
    if (!doc.documentElement) {
      return { ok: false, message: T.unknownError, loc: null };
    }
    var declMatch = /^\s*<\?xml[^>]*\?>/.exec(text);
    return { ok: true, tree: convertNode(doc.documentElement), declaration: declMatch ? declMatch[0] : "" };
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
    toggle.className = "xml-toggle";
    toggle.textContent = "▾";
    toggle.setAttribute("aria-label", T.toggleAria);
    toggle.setAttribute("aria-expanded", "true");
    toggle.addEventListener("click", function () {
      var collapsed = node.classList.toggle("is-collapsed");
      toggle.textContent = collapsed ? "▸" : "▾";
      toggle.setAttribute("aria-expanded", String(!collapsed));
      renderOutputGutter();
    });
    return toggle;
  }

  function appendAttrs(row, attrs) {
    attrs.forEach(function (pair) {
      var space = document.createElement("span");
      space.className = "xml-punct";
      space.textContent = " ";
      row.appendChild(space);

      var nameSpan = document.createElement("span");
      nameSpan.className = "xml-attr-name";
      nameSpan.textContent = pair[0];
      nameSpan.dataset.raw = pair[0];
      row.appendChild(nameSpan);

      var eq = document.createElement("span");
      eq.className = "xml-punct";
      eq.textContent = "=";
      row.appendChild(eq);

      var valSpan = document.createElement("span");
      valSpan.className = "xml-attr-value";
      var valText = '"' + pair[1] + '"';
      valSpan.textContent = valText;
      valSpan.dataset.raw = valText;
      row.appendChild(valSpan);
    });
  }

  function isOnlyText(children) {
    return children.length === 1 && children[0].type === "text";
  }
  function isOnlyCdata(children) {
    return children.length === 1 && children[0].type === "cdata";
  }

  function buildNode(node) {
    var wrapper = document.createElement("div");
    wrapper.className = "xml-node";

    if (node.type === "comment") {
      var crow = document.createElement("div");
      crow.className = "xml-row";
      var cspan = document.createElement("span");
      cspan.className = "xml-comment";
      cspan.textContent = "<!--" + node.text + "-->";
      cspan.dataset.raw = node.text;
      crow.appendChild(cspan);
      wrapper.appendChild(crow);
      return wrapper;
    }

    if (node.type === "cdata") {
      var drow = document.createElement("div");
      drow.className = "xml-row";
      var dspan = document.createElement("span");
      dspan.className = "xml-cdata";
      dspan.textContent = "<![CDATA[" + node.text + "]]>";
      dspan.dataset.raw = node.text;
      drow.appendChild(dspan);
      wrapper.appendChild(drow);
      return wrapper;
    }

    if (node.type === "text") {
      var trow = document.createElement("div");
      trow.className = "xml-row";
      var tspan = document.createElement("span");
      tspan.className = "xml-text";
      var trimmed = node.text.trim();
      tspan.textContent = trimmed;
      tspan.dataset.raw = trimmed;
      trow.appendChild(tspan);
      wrapper.appendChild(trow);
      return wrapper;
    }

    // element
    var row = document.createElement("div");
    row.className = "xml-row";
    wrapper.appendChild(row);

    var openLt = document.createElement("span");
    openLt.className = "xml-bracket";
    openLt.textContent = "<";
    row.appendChild(openLt);

    var tagSpan = document.createElement("span");
    tagSpan.className = "xml-tag";
    tagSpan.textContent = node.tag;
    tagSpan.dataset.raw = node.tag;
    row.appendChild(tagSpan);

    appendAttrs(row, node.attrs);

    var children = node.children;

    if (children.length === 0) {
      var selfClose = document.createElement("span");
      selfClose.className = "xml-bracket";
      selfClose.textContent = " />";
      row.appendChild(selfClose);
      return wrapper;
    }

    if (isOnlyText(children) || isOnlyCdata(children)) {
      var closeGt = document.createElement("span");
      closeGt.className = "xml-bracket";
      closeGt.textContent = ">";
      row.appendChild(closeGt);

      var leaf = children[0];
      var leafSpan = document.createElement("span");
      var raw = leaf.text.trim();
      if (leaf.type === "cdata") {
        leafSpan.className = "xml-cdata";
        leafSpan.textContent = "<![CDATA[" + leaf.text + "]]>";
      } else {
        leafSpan.className = "xml-text";
        leafSpan.textContent = raw;
      }
      leafSpan.dataset.raw = raw;
      row.appendChild(leafSpan);

      var closeTag = document.createElement("span");
      closeTag.className = "xml-bracket";
      closeTag.textContent = "</" + node.tag + ">";
      row.appendChild(closeTag);
      return wrapper;
    }

    // 컨테이너 (자식 엘리먼트/혼합 콘텐츠가 여러 개)
    wrapper.classList.add("is-collapsible");
    toggleRegistry.set(wrapper, createToggle(wrapper));

    var closeGt2 = document.createElement("span");
    closeGt2.className = "xml-bracket";
    closeGt2.textContent = ">";
    row.appendChild(closeGt2);

    var previewSpan = document.createElement("span");
    previewSpan.className = "xml-preview";
    previewSpan.textContent = " … " + T.previewSuffix(children.length) + " </" + node.tag + ">";
    row.appendChild(previewSpan);

    var childrenWrap = document.createElement("div");
    childrenWrap.className = "xml-children";
    children.forEach(function (child) {
      childrenWrap.appendChild(buildNode(child));
    });
    wrapper.appendChild(childrenWrap);

    var closeRow = document.createElement("div");
    closeRow.className = "xml-row xml-close-row";
    var closeSpan = document.createElement("span");
    closeSpan.className = "xml-bracket";
    closeSpan.textContent = "</" + node.tag + ">";
    closeRow.appendChild(closeSpan);
    wrapper.appendChild(closeRow);

    return wrapper;
  }

  function renderTree(tree) {
    toggleRegistry = new Map();
    els.output.innerHTML = "";
    var treeRoot = document.createElement("div");
    treeRoot.className = "xml-tree";
    treeRoot.appendChild(buildNode(tree));
    els.output.appendChild(treeRoot);
    renderOutputGutter();
  }

  function renderPlaceholder() {
    els.output.innerHTML = '<p class="jf-placeholder">' + escapeHtml(T.outputPlaceholder) + "</p>";
    renderOutputGutter();
  }

  function renderErrorBox(parsed) {
    var lines = [];
    lines.push("<p><strong>" + escapeHtml(T.errorBoxTitle) + "</strong></p>");
    if (parsed.loc) {
      lines.push("<p>" + escapeHtml(T.errorLocation(parsed.loc.line, parsed.loc.column)) + "</p>");
    }
    lines.push("<p><code>" + escapeHtml(parsed.message || T.unknownError) + "</code></p>");
    els.output.innerHTML = '<div class="jf-error-box">' + lines.join("") + "</div>";
    renderOutputGutter();
  }

  // ---------------------------------------------------------------
  // 2-1. 결과 화면 줄 번호
  // ---------------------------------------------------------------

  function collectVisibleOutputRows() {
    var treeRoot = els.output.querySelector(".xml-tree");
    var items = [];
    if (!treeRoot) return items;

    function walkNode(node) {
      var row = node.querySelector(":scope > .xml-row:not(.xml-close-row)");
      if (row) items.push({ row: row, node: node.classList.contains("is-collapsible") ? node : null });
      if (!node.classList.contains("is-collapsed")) {
        var childrenWrap = node.querySelector(":scope > .xml-children");
        if (childrenWrap) {
          Array.prototype.forEach.call(childrenWrap.children, function (child) {
            if (child.classList.contains("xml-node")) walkNode(child);
          });
        }
        var closeRow = node.querySelector(":scope > .xml-close-row");
        if (closeRow) items.push({ row: closeRow, node: null });
      }
    }

    Array.prototype.forEach.call(treeRoot.children, function (child) {
      if (child.classList.contains("xml-node")) walkNode(child);
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
      if (toggle) toggleSlot.appendChild(toggle);
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
  // 3. 상태 표시
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
  // 3-1. 입력창 줄 번호
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
  // 3-2. 입력창 검색
  // ---------------------------------------------------------------

  function escapeHtmlText(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

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
    if (!ranges.length) return escapeHtmlText(text);
    var html = "";
    var cursor = 0;
    ranges.forEach(function (r, idx) {
      html += escapeHtmlText(text.slice(cursor, r[0]));
      var cls = "xml-search-match" + (idx === activeIndex ? " is-active" : "");
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
  // 4. 직렬화(포맷/압축 출력용)
  // ---------------------------------------------------------------

  function escapeXmlText(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function escapeXmlAttr(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }

  function attrsToString(attrs) {
    return attrs.map(function (p) { return " " + p[0] + '="' + escapeXmlAttr(p[1]) + '"'; }).join("");
  }

  function serializeNode(node, indent, level, pretty) {
    var pad = pretty ? indent.repeat(level) : "";
    var nl = pretty ? "\n" : "";
    if (node.type === "comment") return pad + "<!--" + node.text + "-->" + nl;
    if (node.type === "cdata") return pad + "<![CDATA[" + node.text + "]]>" + nl;
    if (node.type === "text") {
      var t = node.text.trim();
      return t ? pad + escapeXmlText(t) + nl : "";
    }
    var attrStr = attrsToString(node.attrs);
    if (node.children.length === 0) {
      return pad + "<" + node.tag + attrStr + " />" + nl;
    }
    if (isOnlyText(node.children)) {
      return pad + "<" + node.tag + attrStr + ">" + escapeXmlText(node.children[0].text.trim()) + "</" + node.tag + ">" + nl;
    }
    if (isOnlyCdata(node.children)) {
      return pad + "<" + node.tag + attrStr + "><![CDATA[" + node.children[0].text + "]]></" + node.tag + ">" + nl;
    }
    var out = pad + "<" + node.tag + attrStr + ">" + nl;
    node.children.forEach(function (child) {
      out += serializeNode(child, indent, level + 1, pretty);
    });
    out += pad + "</" + node.tag + ">" + nl;
    return out;
  }

  function serializeXml(tree, declaration, indent, pretty) {
    var head = declaration ? declaration + (pretty ? "\n" : "") : "";
    return head + serializeNode(tree, indent, 0, pretty);
  }

  function getIndentStr() {
    var v = els.indentSelect.value;
    return v === "tab" ? "\t" : " ".repeat(parseInt(v, 10));
  }

  // ---------------------------------------------------------------
  // 5. 실행 파이프라인
  // ---------------------------------------------------------------

  function process() {
    var text = els.input.value;
    var parsed = tryParse(text);
    clearSearch();

    if (parsed.empty) {
      state.isValid = false;
      state.parsedTree = undefined;
      setStatus("idle", T.statusIdleText, T.statusIdleTop);
      renderPlaceholder();
      renderGutter(text);
      setToolbarEnabled(false);
      return;
    }

    if (!parsed.ok) {
      state.isValid = false;
      state.parsedTree = undefined;
      var detail = parsed.loc ? T.detailInvalid(parsed.loc.line, parsed.loc.column) : T.detailInvalidGeneric;
      setStatus("invalid", T.statusInvalidText, T.statusInvalidTop, detail);
      renderErrorBox(parsed);
      renderGutter(text);
      setToolbarEnabled(false);
      return;
    }

    state.isValid = true;
    state.parsedTree = parsed.tree;
    state.declaration = parsed.declaration;
    setStatus("valid", T.statusValidText, T.statusValidTop);
    renderGutter(text);
    renderTree(parsed.tree);
    setToolbarEnabled(true);
  }

  function scheduleProcess() {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(function () {
      process();
      if (state.isValid) {
        switchTab("output");
      }
    }, 250);
  }

  // ---------------------------------------------------------------
  // 6. 툴바 동작
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
    if (state.isValid) {
      els.input.value = serializeXml(state.parsedTree, state.declaration, getIndentStr(), true).replace(/\n$/, "");
      process();
    }
    refreshInputSearchOverlay();
  });

  els.btnSample.addEventListener("click", function () {
    els.input.value = SAMPLE_XML;
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
    copyToClipboard(serializeXml(state.parsedTree, state.declaration, getIndentStr(), true).replace(/\n$/, ""));
    flashButton(els.btnCopy, T.copied);
  });

  els.btnCopyMinify.addEventListener("click", function () {
    if (!state.isValid) return;
    copyToClipboard(serializeXml(state.parsedTree, state.declaration, "", false));
    flashButton(els.btnCopyMinify, T.copied);
  });

  els.btnDownload.addEventListener("click", function () {
    if (!state.isValid) return;
    var text = serializeXml(state.parsedTree, state.declaration, getIndentStr(), true).replace(/\n$/, "");
    var blob = new Blob([text], { type: "application/xml" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "formatted.xml";
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
    var nodes = els.output.querySelectorAll(".xml-node.is-collapsible");
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
  // 7. 결과 검색 (태그명/속성/텍스트)
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

  function unwrapQuotes(raw) {
    if (raw.length >= 2 && raw.charAt(0) === '"' && raw.charAt(raw.length - 1) === '"') {
      return { text: raw.slice(1, -1), offset: 1 };
    }
    return { text: raw, offset: 0 };
  }

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
      var re = new RegExp(query, "gi");
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
      html += '<mark class="xml-search-match">' + escapeHtml(raw.slice(r[0], r[1])) + "</mark>";
      cursor = r[1];
    });
    html += escapeHtml(raw.slice(cursor));
    return html;
  }

  function runSearch(query) {
    var searchables = els.output.querySelectorAll(".xml-tag, .xml-attr-name, .xml-attr-value, .xml-text, .xml-comment, .xml-cdata");
    var mode = els.searchMode ? els.searchMode.value : "contains";

    var regexError = null;
    if (mode === "regex" && query) {
      try {
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
        el.textContent = el.classList.contains("xml-attr-value") ? '"' + raw + '"' : raw;
        return;
      }
      var display = el.classList.contains("xml-attr-value") ? '"' + raw + '"' : raw;
      var offset = el.classList.contains("xml-attr-value") ? 1 : 0;
      var ranges;
      try {
        ranges = computeMatchRanges(display, mode, query);
      } catch (e) {
        ranges = [];
      }
      var html = buildHighlightedHtml(display, ranges);
      if (html) {
        el.innerHTML = html;
      } else {
        el.textContent = display;
      }
    });

    state.matches = Array.prototype.slice.call(els.output.querySelectorAll(".xml-search-match"));
    state.activeMatchIndex = state.matches.length > 0 ? 0 : -1;
    focusActiveMatch(true);
    updateSearchCount(regexError ? T.regexError : null);
  }

  function expandAncestors(el) {
    var node = el.closest(".xml-node");
    while (node) {
      if (node.classList.contains("is-collapsed")) {
        node.classList.remove("is-collapsed");
        var toggle = toggleRegistry.get(node);
        if (toggle) {
          toggle.textContent = "▾";
          toggle.setAttribute("aria-expanded", "true");
        }
      }
      var parent = node.parentElement ? node.parentElement.closest(".xml-node") : null;
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
  // 8. 탭 전환
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
  // 9. 초기화
  // ---------------------------------------------------------------

  els.input.value = SAMPLE_XML;
  setToolbarEnabled(false);
  process();
  refreshInputSearchOverlay();
})();
