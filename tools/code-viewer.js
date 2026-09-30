/**
 * 코드 뷰어 / 문법 강조(syntax highlighting)
 * - 오픈소스 Prism.js 라이브러리(MIT 라이선스, tools/vendor/prism-bundle.min.js)를
 *   이 페이지에서만 로드해서 사용한다. 라이브러리는 window.Prism으로 노출된다.
 * - 이 도구는 코드에 문법 강조만 적용할 뿐, 코드가 실제로 컴파일/실행되는지는 검증하지 않는다.
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
      statusIdleText: "Paste some source code", statusIdleTop: "Idle",
      statusValidText: "Highlighted", statusValidTop: "Done",
      outputPlaceholder: "Paste source code on the left to see the highlighted result here.",
      copied: "Copied ✓", regexError: "Regex error",
      libMissing: "Syntax highlighting library failed to load. Please refresh the page.",
    },
    ko: {
      statusIdleText: "소스 코드를 붙여넣어주세요", statusIdleTop: "대기 중",
      statusValidText: "강조 완료", statusValidTop: "완료",
      outputPlaceholder: "왼쪽에 소스 코드를 붙여넣으면 강조된 결과가 여기에 표시됩니다.",
      copied: "복사됨 ✓", regexError: "정규식 오류",
      libMissing: "문법 강조 라이브러리를 불러오지 못했습니다. 새로고침해주세요.",
    },
    ja: {
      statusIdleText: "ソースコードを貼り付けてください", statusIdleTop: "待機中",
      statusValidText: "ハイライト完了", statusValidTop: "完了",
      outputPlaceholder: "左側にソースコードを貼り付けると、ハイライトされた結果がここに表示されます。",
      copied: "コピーしました ✓", regexError: "正規表現エラー",
      libMissing: "シンタックスハイライトライブラリの読み込みに失敗しました。ページを再読み込みしてください。",
    },
    zh: {
      statusIdleText: "请粘贴源代码", statusIdleTop: "待处理",
      statusValidText: "高亮完成", statusValidTop: "完成",
      outputPlaceholder: "在左侧粘贴源代码，高亮结果将显示在这里。",
      copied: "已复制 ✓", regexError: "正则表达式错误",
      libMissing: "语法高亮库加载失败，请刷新页面。",
    },
  };
  var T = MESSAGES[LANG];

  var EXT_MAP = {
    plain: "txt", java: "java", csharp: "cs", c: "c", cpp: "cpp", python: "py",
    javascript: "js", typescript: "ts", go: "go", rust: "rs", kotlin: "kt", swift: "swift",
    php: "php", ruby: "rb", markup: "html", css: "css", bash: "sh", json: "json",
    yaml: "yml", markdown: "md", sql: "sql",
  };

  var SAMPLE_CODE =
    "import java.util.*;\n" +
    "import java.util.stream.Collectors;\n" +
    "\n" +
    "/**\n" +
    " * Represents a simple in-memory product catalog for Formix.\n" +
    " */\n" +
    "public class ProductCatalog implements Iterable<Product> {\n" +
    "    private final List<Product> products = new ArrayList<>();\n" +
    "\n" +
    "    public void addProduct(Product product) {\n" +
    "        if (product == null) {\n" +
    "            throw new IllegalArgumentException(\"product must not be null\");\n" +
    "        }\n" +
    "        products.add(product);\n" +
    "    }\n" +
    "\n" +
    "    public Optional<Product> findById(String id) {\n" +
    "        return products.stream()\n" +
    "            .filter(p -> p.getId().equals(id))\n" +
    "            .findFirst();\n" +
    "    }\n" +
    "\n" +
    "    public List<Product> getAvailable() {\n" +
    "        return products.stream()\n" +
    "            .filter(Product::isAvailable)\n" +
    "            .collect(Collectors.toList());\n" +
    "    }\n" +
    "\n" +
    "    @Override\n" +
    "    public Iterator<Product> iterator() {\n" +
    "        return products.iterator();\n" +
    "    }\n" +
    "\n" +
    "    public static void main(String[] args) {\n" +
    "        ProductCatalog catalog = new ProductCatalog();\n" +
    "        catalog.addProduct(new Product(\"json-formatter\", \"JSON Formatter\", 0.0, true));\n" +
    "        catalog.addProduct(new Product(\"sql-formatter\", \"SQL Formatter\", 0.0, true));\n" +
    "\n" +
    "        try {\n" +
    "            for (Product product : catalog) {\n" +
    "                System.out.printf(\"%-20s $%.2f%n\", product.getName(), product.getPrice());\n" +
    "            }\n" +
    "        } catch (Exception e) {\n" +
    "            System.err.println(\"Failed to list products: \" + e.getMessage());\n" +
    "        }\n" +
    "    }\n" +
    "}\n" +
    "\n" +
    "class Product {\n" +
    "    private final String id;\n" +
    "    private final String name;\n" +
    "    private final double price;\n" +
    "    private final boolean available;\n" +
    "\n" +
    "    public Product(String id, String name, double price, boolean available) {\n" +
    "        this.id = id;\n" +
    "        this.name = name;\n" +
    "        this.price = price;\n" +
    "        this.available = available;\n" +
    "    }\n" +
    "\n" +
    "    public String getId() { return id; }\n" +
    "    public String getName() { return name; }\n" +
    "    public double getPrice() { return price; }\n" +
    "    public boolean isAvailable() { return available; }\n" +
    "}\n";

  var els = {
    input: document.getElementById("code-input"),
    status: document.getElementById("code-status"),
    statusTop: document.getElementById("code-status-top"),
    errorDetail: document.getElementById("code-error-detail"),
    errorDetailTop: document.getElementById("code-error-detail-top"),
    output: document.getElementById("code-output"),
    gutter: document.getElementById("code-gutter"),
    gutterInner: document.getElementById("code-gutter-inner"),
    inputHighlight: document.getElementById("code-input-highlight"),
    inputSearchMode: document.getElementById("code-input-search-mode"),
    inputSearchInput: document.getElementById("code-input-search"),
    inputSearchCount: document.getElementById("code-input-search-count"),
    inputSearchPrev: document.getElementById("btn-input-search-prev"),
    inputSearchNext: document.getElementById("btn-input-search-next"),
    inputSearchClear: document.getElementById("btn-input-search-clear"),
    outputGutter: document.getElementById("code-output-gutter"),
    outputGutterInner: document.getElementById("code-output-gutter-inner"),
    tabInput: document.getElementById("tab-input"),
    tabOutput: document.getElementById("tab-output"),
    tabBadge: document.getElementById("tab-output-badge"),
    panelInput: document.getElementById("panel-input"),
    panelOutput: document.getElementById("panel-output"),
    btnFormat: document.getElementById("btn-format"),
    btnSample: document.getElementById("btn-sample"),
    btnClear: document.getElementById("btn-clear"),
    btnCopy: document.getElementById("btn-copy"),
    btnDownload: document.getElementById("btn-download"),
    languageSelect: document.getElementById("code-language-select"),
    searchInput: document.getElementById("code-search"),
    searchMode: document.getElementById("code-search-mode"),
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

  // ---------------------------------------------------------------
  // 1. 문법 강조
  // ---------------------------------------------------------------

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function getLanguage() {
    return els.languageSelect ? els.languageSelect.value : "plain";
  }

  function highlightCode(text, lang) {
    if (lang === "plain" || !window.Prism || !window.Prism.languages[lang]) {
      return escapeHtml(text);
    }
    return window.Prism.highlight(text, window.Prism.languages[lang], lang);
  }

  function renderOutputText(text) {
    els.output.innerHTML = '<pre class="code-output-text"></pre>';
    els.output.firstChild.innerHTML = highlightCode(text, getLanguage());
    renderOutputGutter(text);
  }

  function renderPlaceholder() {
    els.output.innerHTML = '<p class="jf-placeholder">' + escapeHtml(T.outputPlaceholder) + "</p>";
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

  function setStatus(kind, text, topText) {
    els.status.className = "status-pill is-" + kind;
    els.status.textContent = text;
    if (els.statusTop) {
      els.statusTop.className = "status-pill is-" + kind;
      els.statusTop.textContent = topText || text;
    }
    if (els.tabBadge) els.tabBadge.className = "jf-tab-badge is-" + kind;
    if (els.errorDetail) els.errorDetail.textContent = "";
    if (els.errorDetailTop) els.errorDetailTop.textContent = "";
  }

  function setToolbarEnabled(enabled) {
    [els.btnCopy, els.btnDownload].forEach(function (el) {
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

    var lang = getLanguage();
    if (lang !== "plain" && (!window.Prism || !window.Prism.languages)) {
      state.isValid = false;
      setStatus("invalid", T.libMissing, T.statusIdleTop);
      renderGutter(text);
      setToolbarEnabled(false);
      return;
    }

    try {
      state.isValid = true;
      state.outputText = text;
      setStatus("valid", T.statusValidText, T.statusValidTop);
      renderGutter(text);
      renderOutputText(text);
      setToolbarEnabled(true);
    } catch (e) {
      // Prism 토크나이저가 예상치 못한 입력에서 예외를 던지는 극히 드문 경우에도
      // 최소한 원문은 그대로 보여준다.
      state.isValid = true;
      state.outputText = text;
      setStatus("valid", T.statusValidText, T.statusValidTop);
      renderGutter(text);
      els.output.innerHTML = '<pre class="code-output-text"></pre>';
      els.output.firstChild.textContent = text;
      renderOutputGutter(text);
      setToolbarEnabled(true);
    }
  }

  function scheduleProcess() {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(function () {
      process();
    }, 300);
  }

  // ---------------------------------------------------------------
  // 2. 입력창 줄 번호
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
  // 3. 입력창 검색
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
  // 4. 툴바 동작
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
    els.input.value = SAMPLE_CODE;
    if (els.languageSelect) els.languageSelect.value = "java";
    process();
    refreshInputSearchOverlay();
  });

  els.btnClear.addEventListener("click", function () {
    els.input.value = "";
    els.input.focus();
    process();
    refreshInputSearchOverlay();
  });

  if (els.languageSelect) {
    els.languageSelect.addEventListener("change", function () {
      process();
    });
  }

  els.btnCopy.addEventListener("click", function () {
    if (!state.isValid) return;
    copyToClipboard(state.outputText);
    flashButton(els.btnCopy, T.copied);
  });

  els.btnDownload.addEventListener("click", function () {
    if (!state.isValid) return;
    var ext = EXT_MAP[getLanguage()] || "txt";
    var blob = new Blob([state.outputText], { type: "text/plain" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "code." + ext;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // ---------------------------------------------------------------
  // 5. 탭 전환
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
  // 6. 초기화
  // ---------------------------------------------------------------

  els.input.value = SAMPLE_CODE;
  if (els.languageSelect) els.languageSelect.value = "java";
  setToolbarEnabled(false);
  process();
  refreshInputSearchOverlay();
})();
