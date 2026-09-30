/**
 * 숫자 읽기 변환기 (Number Reader)
 * - 외부 라이브러리를 사용하지 않는다. 숫자 → 문자 변환은 규칙이 명확한 순수 알고리즘이므로
 *   이 파일 안에서 직접 구현한다(벤더링 불필요).
 * - 입력값은 서버로 전송되지 않고 이 파일 안에서만(브라우저 내에서) 처리됩니다.
 * - 지원 모드: 일반(기수), 서수, 전화·계좌번호(자릿수별), 시간, 날짜, 화폐
 * - 지원 언어별 표기 체계:
 *   ko: 한자어/고유어(0~99)/갖은자
 *   en: 표준 영어 숫자 표기
 *   ja: 漢数字(標準)/大字(갖은자 스타일)
 *   zh: 小写/大写(재무용)
 */
(function () {
  "use strict";

  var LANG = (function () {
    var l = (document.documentElement.getAttribute("lang") || "en").slice(0, 2).toLowerCase();
    return { en: 1, ko: 1, ja: 1, zh: 1 }[l] ? l : "en";
  })();

  // ---------------------------------------------------------------
  // 0. i18n 메시지
  // ---------------------------------------------------------------
  var MESSAGES = {
    en: {
      statusIdleText: "Enter a number (one per line)", statusIdleTop: "Idle",
      statusValidText: "Converted", statusValidTop: "Done",
      statusPartialText: "Converted (some lines skipped)", statusPartialTop: "Partial",
      outputPlaceholder: "Enter numbers on the left (one per line) to see the reading here.",
      copied: "Copied ✓", regexError: "Regex error",
      lineError: "Could not read this line",
      modeLabel: "Mode", styleLabel: "Style",
      mode_cardinal: "Number (cardinal)", mode_ordinal: "Ordinal", mode_digits: "Phone / account number",
      mode_time: "Time", mode_date: "Date", mode_currency: "Currency",
      placeholder_cardinal: "e.g. 1234567890 (one per line)\nSupports negative numbers and decimals.",
      placeholder_ordinal: "e.g. 21 (one per line, non-negative whole numbers)",
      placeholder_digits: "e.g. 010-1234-5678 (one per line)",
      placeholder_time: "e.g. 14:30 or 9:05:12 (one per line, 24-hour)",
      placeholder_date: "e.g. 2026-09-30 (one per line, YYYY-MM-DD)",
      placeholder_currency: "e.g. 12345.67 (one per line)",
      style_cardinal_all: "All styles (compare)", style_cardinal_sino: "Standard (Sino)", style_cardinal_native: "Native (0–99)", style_cardinal_formal: "Formal (anti-fraud)",
      style_cardinal_standard: "Standard", style_cardinal_formaljp: "Formal (大字)",
      style_cardinal_lower: "Standard (小写)", style_cardinal_upper: "Formal (大写)",
      style_cardinal_words: "Words",
      style_ordinal_all: "All styles (compare)", style_ordinal_native: "Native", style_ordinal_sino: "Sino (제N)",
      style_ordinal_prefix: "Prefix (第N)", style_ordinal_suffix: "Suffix (N番目)",
      style_ordinal_words: "Words",
      style_time_civilian: "12-hour (AM/PM)", style_time_24h: "24-hour",
      style_currency_sino: "Standard", style_currency_formal: "Formal (anti-fraud)",
      style_currency_lower: "Standard (小写)", style_currency_upper: "Formal (大写)",
      style_currency_words: "Words",
      hint: "Tip. Everything runs locally in your browser — nothing you type is sent to a server. " +
            "Large integers of any length are supported. Some very informal or dialectal readings (for example, " +
            "certain day-of-month readings in Japanese) are simplified for consistency.",
      usage_h2_extra: null,
    },
    ko: {
      statusIdleText: "숫자를 입력해주세요 (한 줄에 하나씩)", statusIdleTop: "대기 중",
      statusValidText: "변환 완료", statusValidTop: "완료",
      statusPartialText: "일부 줄은 변환하지 못했습니다", statusPartialTop: "일부 완료",
      outputPlaceholder: "왼쪽에 숫자를 입력하면(한 줄에 하나씩) 읽는 법이 여기에 표시됩니다.",
      copied: "복사됨 ✓", regexError: "정규식 오류",
      lineError: "이 줄은 변환할 수 없습니다",
      modeLabel: "모드", styleLabel: "표기 방식",
      mode_cardinal: "일반 숫자(기수)", mode_ordinal: "서수", mode_digits: "전화·계좌번호",
      mode_time: "시간", mode_date: "날짜", mode_currency: "화폐",
      placeholder_cardinal: "예: 1234567890 (한 줄에 하나씩)\n음수, 소수점도 지원합니다.",
      placeholder_ordinal: "예: 21 (한 줄에 하나씩, 0 이상의 정수)",
      placeholder_digits: "예: 010-1234-5678 (한 줄에 하나씩)",
      placeholder_time: "예: 14:30 또는 9:05:12 (한 줄에 하나씩, 24시간제)",
      placeholder_date: "예: 2026-09-30 (한 줄에 하나씩, YYYY-MM-DD)",
      placeholder_currency: "예: 12345.67 (한 줄에 하나씩)",
      style_cardinal_all: "전체 비교", style_cardinal_sino: "한자어(기본)", style_cardinal_native: "고유어(0~99)", style_cardinal_formal: "갖은자(금액·위변조 방지용)",
      style_cardinal_standard: "표준", style_cardinal_formaljp: "大字(갖은자)",
      style_cardinal_lower: "小写(기본)", style_cardinal_upper: "大写(공식)",
      style_cardinal_words: "단어",
      style_ordinal_all: "전체 비교", style_ordinal_native: "고유어 서수", style_ordinal_sino: "한자어 서수(제N)",
      style_ordinal_prefix: "第N", style_ordinal_suffix: "N番目",
      style_ordinal_words: "단어",
      style_time_civilian: "12시간제(오전/오후)", style_time_24h: "24시간제",
      style_currency_sino: "한자어(기본)", style_currency_formal: "갖은자(위변조 방지용)",
      style_currency_lower: "小写(기본)", style_currency_upper: "大写(공식)",
      style_currency_words: "단어",
      hint: "Tip. 모든 변환은 브라우저 안에서만 이뤄지며, 입력한 내용은 서버로 전송되지 않습니다. " +
            "자릿수에 관계없이 아주 큰 정수도 지원합니다. 일본어 날짜의 일부 관용적 읽기(1일=ついたち 등)처럼 " +
            "매우 구어적이거나 방언적인 읽기는 일관성을 위해 단순화되어 있습니다.",
    },
    ja: {
      statusIdleText: "数値を入力してください（1行に1つ）", statusIdleTop: "待機中",
      statusValidText: "変換完了", statusValidTop: "完了",
      statusPartialText: "一部の行は変換できませんでした", statusPartialTop: "一部完了",
      outputPlaceholder: "左側に数値を入力すると（1行に1つ）、読み方がここに表示されます。",
      copied: "コピーしました ✓", regexError: "正規表現エラー",
      lineError: "この行は変換できません",
      modeLabel: "モード", styleLabel: "表記方式",
      mode_cardinal: "数値（基数）", mode_ordinal: "序数", mode_digits: "電話・口座番号",
      mode_time: "時刻", mode_date: "日付", mode_currency: "通貨",
      placeholder_cardinal: "例: 1234567890（1行に1つ）\n負の数・小数にも対応しています。",
      placeholder_ordinal: "例: 21（1行に1つ、0以上の整数）",
      placeholder_digits: "例: 010-1234-5678（1行に1つ）",
      placeholder_time: "例: 14:30 または 9:05:12（1行に1つ、24時間制）",
      placeholder_date: "例: 2026-09-30（1行に1つ、YYYY-MM-DD）",
      placeholder_currency: "例: 12345.67（1行に1つ）",
      style_cardinal_all: "全表記を比較", style_cardinal_sino: "標準", style_cardinal_native: "標準", style_cardinal_formal: "大字（証書用）",
      style_cardinal_standard: "標準", style_cardinal_formaljp: "大字（証書用）",
      style_cardinal_lower: "標準", style_cardinal_upper: "大写",
      style_cardinal_words: "単語",
      style_ordinal_all: "全表記を比較", style_ordinal_native: "標準", style_ordinal_sino: "標準",
      style_ordinal_prefix: "第N", style_ordinal_suffix: "N番目",
      style_ordinal_words: "単語",
      style_time_civilian: "12時間制（午前/午後）", style_time_24h: "24時間制",
      style_currency_sino: "標準", style_currency_formal: "大字（証書用）",
      style_currency_lower: "標準", style_currency_upper: "大写",
      style_currency_words: "単語",
      hint: "Tip. すべての変換はブラウザ内でのみ行われ、入力内容はサーバーに送信されません。" +
            "桁数に関わらず非常に大きな整数にも対応しています。日付の一部の慣用的な読み方（1日=ついたち 等）のような" +
            "非常に口語的・方言的な読みは、一貫性のため簡略化しています。",
    },
    zh: {
      statusIdleText: "请输入数字（每行一个）", statusIdleTop: "待处理",
      statusValidText: "转换完成", statusValidTop: "完成",
      statusPartialText: "部分行未能转换", statusPartialTop: "部分完成",
      outputPlaceholder: "在左侧输入数字（每行一个），读法将显示在这里。",
      copied: "已复制 ✓", regexError: "正则表达式错误",
      lineError: "无法转换此行",
      modeLabel: "模式", styleLabel: "表示方式",
      mode_cardinal: "数字（基数）", mode_ordinal: "序数", mode_digits: "电话·账号",
      mode_time: "时间", mode_date: "日期", mode_currency: "货币",
      placeholder_cardinal: "例如: 1234567890（每行一个）\n支持负数和小数。",
      placeholder_ordinal: "例如: 21（每行一个，非负整数）",
      placeholder_digits: "例如: 010-1234-5678（每行一个）",
      placeholder_time: "例如: 14:30 或 9:05:12（每行一个，24小时制）",
      placeholder_date: "例如: 2026-09-30（每行一个，YYYY-MM-DD）",
      placeholder_currency: "例如: 12345.67（每行一个）",
      style_cardinal_all: "全部对比", style_cardinal_sino: "小写(默认)", style_cardinal_native: "小写(默认)", style_cardinal_formal: "大写(财务用)",
      style_cardinal_standard: "小写(默认)", style_cardinal_formaljp: "大写",
      style_cardinal_lower: "小写(默认)", style_cardinal_upper: "大写(财务用)",
      style_cardinal_words: "单词",
      style_ordinal_all: "全部对比", style_ordinal_native: "标准", style_ordinal_sino: "标准",
      style_ordinal_prefix: "第N", style_ordinal_suffix: "第N",
      style_ordinal_words: "单词",
      style_time_civilian: "12小时制(上午/下午)", style_time_24h: "24小时制",
      style_currency_sino: "小写(默认)", style_currency_formal: "大写(财务用)",
      style_currency_lower: "小写(默认)", style_currency_upper: "大写(财务用)",
      style_currency_words: "单词",
      hint: "提示。所有转换均在浏览器本地完成，您输入的内容不会发送到服务器。" +
            "支持任意位数的大整数。部分非常口语化或方言化的读法（例如日语中某些日期的习惯读法）" +
            "为保持一致性已做简化处理。",
    },
  };
  var T = MESSAGES[LANG];

  // ---------------------------------------------------------------
  // 1. 공통 유틸
  // ---------------------------------------------------------------

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // 정수 문자열을 4자리(또는 3자리) 단위로 상위 그룹부터 분할
  function splitGroups(s, size) {
    var groups = [];
    while (s.length > 0) {
      if (s.length <= size) {
        groups.unshift(s);
        s = "";
      } else {
        groups.unshift(s.slice(-size));
        s = s.slice(0, -size);
      }
    }
    return groups;
  }

  function stripLeadingZeros(s) {
    var stripped = s.replace(/^0+(?=\d)/, "");
    return stripped === "" ? "0" : stripped;
  }

  // "-123.45" 같은 문자열을 {neg, intPart, decPart} 로 분해. 형식이 아니면 null.
  function parseSignedDecimal(raw) {
    var s = raw.trim();
    if (s === "") return null;
    var neg = false;
    if (s[0] === "-") { neg = true; s = s.slice(1); }
    else if (s[0] === "+") { s = s.slice(1); }
    s = s.replace(/,/g, ""); // 천단위 구분 콤마 허용
    var parts = s.split(".");
    if (parts.length > 2) return null;
    var intPart = parts[0] === "" ? "0" : parts[0];
    var decPart = parts.length === 2 ? parts[1] : "";
    if (!/^\d+$/.test(intPart)) return null;
    if (decPart && !/^\d+$/.test(decPart)) return null;
    return { neg: neg, intPart: stripLeadingZeros(intPart), decPart: decPart };
  }

  // ---------------------------------------------------------------
  // 2. 한자어 계열(한국어/일본어/중국어) 공통 그룹 변환 엔진
  //    base-10000 그룹핑 + 그룹 내부 십/백/천 단위. 4개 언어 스타일이 모두 이 엔진을 공유한다.
  // ---------------------------------------------------------------

  // omitOneRule:
  //  - "unit"        : 십/백/천(十/百/千) 앞의 "1"은 자리와 상관없이 항상 생략 (한국어/일본어 표준 표기)
  //  - "leadingTenOnly": 숫자 전체의 맨 앞자리가 "십(十)"일 때만 "1"을 생략, 그 외(백/천 앞이나 뒷자리)에는 항상 표기
  //                     (중국어 표준 표기: 15=十五 이지만 115=一百一十五, 100=一百)
  //  - "never"       : 절대 생략하지 않음 (갖은자/大字/大写 — 위변조 방지 목적이 생략을 금지한다)
  function convertChunk(chunk, cfg, state) {
    var len = chunk.length;
    var out = "";
    for (var i = 0; i < len; i++) {
      var digit = parseInt(chunk[i], 10);
      if (digit === 0) continue;
      var power = len - 1 - i; // 0=일의자리, 1=십, 2=백, 3=천
      var unit = cfg.unitSmall[power] || "";
      var omit = false;
      if (digit === 1 && power > 0) {
        if (cfg.omitOneRule === "unit") omit = true;
        else if (cfg.omitOneRule === "leadingTenOnly") omit = power === 1 && !state.started;
      }
      out += omit ? unit : cfg.digitChars[digit] + unit;
      state.started = true;
    }
    return out;
  }

  function convertGroupedInteger(intPart, cfg) {
    var digitsStr = stripLeadingZeros(intPart);
    if (digitsStr === "0") return cfg.digitChars[0];
    var groups = splitGroups(digitsStr, 4);
    var n = groups.length;
    if (n > cfg.unitBig.length) return null; // 지원하는 최대 자릿수(약 10^20)를 넘으면 잘못된 결과 대신 오류로 처리
    var out = "";
    var state = { started: false };
    for (var gi = 0; gi < n; gi++) {
      var chunkStr = convertChunk(groups[gi], cfg, state);
      if (chunkStr === "") continue; // 해당 그룹이 0000이면 건너뜀
      var bigIdx = n - 1 - gi;
      out += chunkStr + (cfg.unitBig[bigIdx] || "");
    }
    return out;
  }

  function groupedCardinal(raw, cfg) {
    var parsed = parseSignedDecimal(raw);
    if (!parsed) return null;
    var out = convertGroupedInteger(parsed.intPart, cfg);
    if (out === null) return null;
    if (parsed.decPart) {
      out += cfg.pointWord + parsed.decPart.split("").map(function (d) {
        return cfg.digitChars[parseInt(d, 10)];
      }).join("");
    }
    if (parsed.neg) out = cfg.negWord + out;
    return out;
  }

  // 언어별 숫자/단위 문자 세트 -----------------------------------------

  var KO_SINO = {
    digitChars: ["영", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"],
    unitSmall: ["", "십", "백", "천"],
    unitBig: ["", "만", "억", "조", "경"],
    negWord: "마이너스 ", pointWord: "점", omitOneRule: "unit",
  };
  var KO_FORMAL = {
    digitChars: ["零", "壹", "貳", "參", "肆", "伍", "陸", "柒", "捌", "玖"],
    unitSmall: ["", "拾", "佰", "仟"],
    unitBig: ["", "萬", "億", "兆", "京"],
    negWord: "마이너스 ", pointWord: "點", omitOneRule: "never",
  };
  var JA_STD = {
    digitChars: ["〇", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
    unitSmall: ["", "十", "百", "千"],
    unitBig: ["", "万", "億", "兆", "京"],
    negWord: "マイナス", pointWord: "点", omitOneRule: "unit",
  };
  var JA_FORMAL = {
    digitChars: ["零", "壱", "弐", "参", "四", "伍", "六", "七", "八", "九"],
    unitSmall: ["", "拾", "百", "阡"],
    unitBig: ["", "萬", "億", "兆", "京"],
    negWord: "マイナス", pointWord: "点", omitOneRule: "never",
  };
  var ZH_LOWER = {
    digitChars: ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"],
    unitSmall: ["", "十", "百", "千"],
    unitBig: ["", "万", "亿", "兆", "京"],
    negWord: "负", pointWord: "点", omitOneRule: "leadingTenOnly",
  };
  var ZH_UPPER = {
    digitChars: ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"],
    unitSmall: ["", "拾", "佰", "仟"],
    unitBig: ["", "万", "亿", "兆", "京"],
    negWord: "负", pointWord: "点", omitOneRule: "never",
  };

  // ---------------------------------------------------------------
  // 3. 한국어 고유어(순우리말, 0~99) 기수/서수
  // ---------------------------------------------------------------

  var KO_NATIVE_ONES = ["", "하나", "둘", "셋", "넷", "다섯", "여섯", "일곱", "여덟", "아홉"];
  var KO_NATIVE_TENS = ["", "열", "스물", "서른", "마흔", "쉰", "예순", "일흔", "여든", "아흔"];
  var KO_NATIVE_ONES_MOD = ["", "한", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉"]; // 관형형(뒤에 단위/째가 붙을 때)
  var KO_ORDINAL_FIXED = ["", "첫째", "둘째", "셋째", "넷째", "다섯째", "여섯째", "일곱째", "여덟째", "아홉째", "열째"];

  function koNativeCardinal(n) {
    if (n === 0) return "영";
    if (n > 99) return null;
    var tens = Math.floor(n / 10), ones = n % 10;
    return (tens > 0 ? KO_NATIVE_TENS[tens] : "") + (ones > 0 ? KO_NATIVE_ONES[ones] : "");
  }

  function koNativeOrdinal(n) {
    if (n < 1 || n > 99) return null;
    if (n <= 10) return KO_ORDINAL_FIXED[n];
    var tens = Math.floor(n / 10), ones = n % 10;
    var tensWord = ones === 0 && tens === 2 ? "스무" : KO_NATIVE_TENS[tens];
    return tensWord + (ones > 0 ? KO_NATIVE_ONES_MOD[ones] + "째" : "째");
  }

  function koSinoOrdinal(n) {
    if (n < 0) return null;
    var w = convertGroupedInteger(String(n), KO_SINO);
    return w === null ? null : "제" + w;
  }

  // ---------------------------------------------------------------
  // 4. 영어 기수/서수
  // ---------------------------------------------------------------

  var EN_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"];
  var EN_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"];
  var EN_SCALES = ["", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion",
    "sextillion", "septillion", "octillion", "nonillion", "decillion"];
  var EN_ORD_MAP = { one: "first", two: "second", three: "third", five: "fifth", eight: "eighth", nine: "ninth", twelve: "twelfth" };

  function enThreeDigitWords(n) {
    var h = Math.floor(n / 100), r = n % 100;
    var out = "";
    if (h > 0) out += EN_ONES[h] + " hundred";
    if (r > 0) {
      if (out) out += " ";
      if (r < 20) out += EN_ONES[r];
      else {
        out += EN_TENS[Math.floor(r / 10)];
        if (r % 10) out += "-" + EN_ONES[r % 10];
      }
    }
    return out;
  }

  function enCardinalInteger(intPart) {
    var digitsStr = stripLeadingZeros(intPart);
    if (digitsStr === "0") return "zero";
    var groups = splitGroups(digitsStr, 3);
    var n = groups.length;
    var parts = [];
    for (var gi = 0; gi < n; gi++) {
      var val = parseInt(groups[gi], 10);
      if (val === 0) continue;
      var scaleIdx = n - 1 - gi;
      var words = enThreeDigitWords(val);
      if (scaleIdx > 0) {
        words += " " + (EN_SCALES[scaleIdx] || ("×10^" + scaleIdx * 3));
      }
      parts.push(words);
    }
    return parts.join(" ");
  }

  function enCardinal(raw) {
    var parsed = parseSignedDecimal(raw);
    if (!parsed) return null;
    var out = enCardinalInteger(parsed.intPart);
    if (parsed.decPart) {
      out += " point " + parsed.decPart.split("").map(function (d) { return EN_ONES[parseInt(d, 10)]; }).join(" ");
    }
    if (parsed.neg) out = "minus " + out;
    return out;
  }

  function enOrdinal(raw) {
    var s = raw.trim();
    if (!/^\d+$/.test(s)) return null;
    var cardinal = enCardinalInteger(stripLeadingZeros(s));
    var words = cardinal.split(" ");
    var last = words[words.length - 1];
    var hyphenParts = last.split("-");
    var lastPart = hyphenParts[hyphenParts.length - 1];
    var newLastPart;
    if (EN_ORD_MAP[lastPart]) newLastPart = EN_ORD_MAP[lastPart];
    else if (/y$/.test(lastPart)) newLastPart = lastPart.slice(0, -1) + "ieth";
    else newLastPart = lastPart + "th";
    hyphenParts[hyphenParts.length - 1] = newLastPart;
    words[words.length - 1] = hyphenParts.join("-");
    return words.join(" ");
  }

  // 영어 연도 읽기(예: 2026 -> "twenty twenty-six", 2000 -> "two thousand", 1905 -> "nineteen oh five")
  function enYearWords(year) {
    if (year < 1000 || year > 9999) return enCardinalInteger(String(year));
    var first2 = Math.floor(year / 100), last2 = year % 100;
    if (year >= 2000 && year <= 2009) {
      return last2 === 0 ? "two thousand" : "two thousand and " + (last2 < 20 ? EN_ONES[last2] : enThreeDigitWords(last2));
    }
    if (last2 === 0) return enThreeDigitWords(first2) + " hundred";
    var firstWords = first2 < 20 ? EN_ONES[first2] : enThreeDigitWords(first2);
    var lastWords;
    if (last2 < 10) lastWords = "oh " + EN_ONES[last2];
    else if (last2 < 20) lastWords = EN_ONES[last2];
    else {
      lastWords = EN_TENS[Math.floor(last2 / 10)];
      if (last2 % 10) lastWords += "-" + EN_ONES[last2 % 10];
    }
    return firstWords + " " + lastWords;
  }

  // ---------------------------------------------------------------
  // 5. 자릿수별 읽기(전화·계좌번호)
  // ---------------------------------------------------------------

  var KO_DIGIT_WORDS = ["공", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"];
  var EN_DIGIT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];

  function digitsLine(raw, lang) {
    var s = raw.trim();
    if (!/\d/.test(s) || /[^0-9\s\-./]/.test(s)) return null;
    var out = "";
    for (var i = 0; i < s.length; i++) {
      var ch = s[i];
      if (/\d/.test(ch)) {
        var d = parseInt(ch, 10);
        var word;
        if (lang === "ko") word = KO_DIGIT_WORDS[d];
        else if (lang === "en") word = EN_DIGIT_WORDS[d];
        else word = JA_STD.digitChars[d]; // ja/zh 모두 한자 숫자로 자리별 표기
        out += word + (lang === "en" ? " " : " ");
      } else if (/\s/.test(ch)) {
        // 공백은 그대로 구분자로 유지
        out += " ";
      } else {
        out += " " + ch + " "; // -, ., / 등 구분자
      }
    }
    return out.replace(/\s+/g, " ").trim();
  }

  // ---------------------------------------------------------------
  // 6. 시간
  // ---------------------------------------------------------------

  function timeLine(raw, lang, style) {
    var s = raw.trim();
    var m = /^(\d{1,2}):(\d{2})(?::(\d{2}))?$/.exec(s);
    if (!m) return null;
    var h = parseInt(m[1], 10), mi = parseInt(m[2], 10), se = m[3] !== undefined ? parseInt(m[3], 10) : null;
    if (h > 23 || mi > 59 || (se !== null && se > 59)) return null;

    if (lang === "ko") {
      var koMinuteWord = mi === 0 ? "정각" : convertGroupedInteger(String(mi), KO_SINO) + "분";
      if (style === "24h") {
        var out = convertGroupedInteger(String(h), KO_SINO) + "시" + koMinuteWord;
        if (se !== null) out += convertGroupedInteger(String(se), KO_SINO) + "초";
        return out;
      }
      var isPM = h >= 12;
      var civilHour = h % 12; if (civilHour === 0) civilHour = 12;
      var hourWord = koNativeCardinal(civilHour) || String(civilHour);
      var res = (isPM ? "오후 " : "오전 ") + hourWord + "시" + koMinuteWord;
      if (se !== null) res += convertGroupedInteger(String(se), KO_SINO) + "초";
      return res;
    }
    if (lang === "en") {
      if (style === "24h") {
        var eo = EN_ONES[h] || enCardinalInteger(String(h));
        var em = mi === 0 ? "hundred" : (mi < 10 ? "oh " + EN_ONES[mi] : enCardinalInteger(String(mi)));
        var r = eo + " " + em;
        if (se !== null) r += " and " + enCardinalInteger(String(se)) + " seconds";
        return r;
      }
      var pm = h >= 12;
      var ch12 = h % 12; if (ch12 === 0) ch12 = 12;
      var hw = enCardinalInteger(String(ch12));
      var mw = mi === 0 ? "o'clock" : (mi < 10 ? "oh " + EN_ONES[mi] : enCardinalInteger(String(mi)));
      var out2 = hw + " " + mw + " " + (pm ? "PM" : "AM");
      if (se !== null) out2 += ", " + enCardinalInteger(String(se)) + " seconds";
      return out2;
    }
    // ja / zh
    var cfg = lang === "ja" ? JA_STD : ZH_LOWER;
    var hourUnit = lang === "ja" ? "時" : "点";
    var minUnit = "分", secUnit = lang === "ja" ? "秒" : "秒";
    var ampmBefore = "";
    var hh = h;
    if (style !== "24h") {
      var isPm2 = h >= 12;
      hh = h % 12; if (hh === 0) hh = 12;
      ampmBefore = lang === "ja" ? (isPm2 ? "午後" : "午前") : (isPm2 ? "下午" : "上午");
    }
    var outJz = ampmBefore + convertGroupedInteger(String(hh), cfg) + hourUnit + convertGroupedInteger(String(mi), cfg) + minUnit;
    if (se !== null) outJz += convertGroupedInteger(String(se), cfg) + secUnit;
    return outJz;
  }

  // ---------------------------------------------------------------
  // 7. 날짜
  // ---------------------------------------------------------------

  var KO_MONTH_EXC = { 6: "유월", 10: "시월" };
  var EN_MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  function dateLine(raw, lang) {
    var s = raw.trim();
    var m = /^(\d{3,4})[-/](\d{1,2})[-/](\d{1,2})$/.exec(s);
    if (!m) return null;
    var y = parseInt(m[1], 10), mo = parseInt(m[2], 10), d = parseInt(m[3], 10);
    if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;

    if (lang === "ko") {
      var monthWord = KO_MONTH_EXC[mo] || (convertGroupedInteger(String(mo), KO_SINO) + "월");
      return convertGroupedInteger(String(y), KO_SINO) + "년 " + monthWord + " " + convertGroupedInteger(String(d), KO_SINO) + "일";
    }
    if (lang === "en") {
      return EN_MONTH_NAMES[mo] + " " + (enOrdinal(String(d)) || d) + ", " + enYearWords(y);
    }
    // ja / zh: 연도는 자리별로 읽는다(일반 관례)
    var cfg = lang === "ja" ? JA_STD : ZH_LOWER;
    var yearDigits = String(y).split("").map(function (c) { return cfg.digitChars[parseInt(c, 10)]; }).join("");
    var yearUnit = "年", monthUnit = lang === "ja" ? "月" : "月", dayUnit = lang === "ja" ? "日" : "日";
    return yearDigits + yearUnit + convertGroupedInteger(String(mo), cfg) + monthUnit + convertGroupedInteger(String(d), cfg) + dayUnit;
  }

  // ---------------------------------------------------------------
  // 8. 화폐
  // ---------------------------------------------------------------

  function currencyLine(raw, lang, style) {
    var parsed = parseSignedDecimal(raw);
    if (!parsed) return null;

    if (lang === "ko") {
      var cfg = style === "formal" ? KO_FORMAL : KO_SINO;
      var koAmountWord = convertGroupedInteger(parsed.intPart, cfg);
      if (koAmountWord === null) return null;
      var out = koAmountWord + "원";
      if (parsed.decPart) {
        var jeon = (parsed.decPart + "00").slice(0, 2);
        if (jeon !== "00") out += " " + convertGroupedInteger(String(parseInt(jeon, 10)), cfg) + "전";
      }
      return parsed.neg ? cfg.negWord + out : out;
    }
    if (lang === "en") {
      var dollars = enCardinalInteger(parsed.intPart);
      var out2 = dollars + (parsed.intPart === "1" ? " dollar" : " dollars");
      if (parsed.decPart) {
        var cents = (parsed.decPart + "00").slice(0, 2);
        if (cents !== "00") {
          var centsN = parseInt(cents, 10);
          out2 += " and " + enCardinalInteger(String(centsN)) + (centsN === 1 ? " cent" : " cents");
        }
      }
      return parsed.neg ? "minus " + out2 : out2;
    }
    if (lang === "ja") {
      var jcfg = style === "formal" ? JA_FORMAL : JA_STD;
      var jaAmountWord = convertGroupedInteger(parsed.intPart, jcfg);
      if (jaAmountWord === null) return null;
      var outJ = jaAmountWord + "円";
      return parsed.neg ? jcfg.negWord + outJ : outJ;
    }
    // zh: 元/角/分, 大写 스타일에는 관례상 "整"을 붙인다
    var zcfg = style === "upper" ? ZH_UPPER : ZH_LOWER;
    var zhAmountWord = convertGroupedInteger(parsed.intPart, zcfg);
    if (zhAmountWord === null) return null;
    var outZ = zhAmountWord + "元";
    if (parsed.decPart) {
      var jiao = parsed.decPart[0] ? parseInt(parsed.decPart[0], 10) : 0;
      var fen = parsed.decPart[1] ? parseInt(parsed.decPart[1], 10) : 0;
      if (jiao > 0) outZ += zcfg.digitChars[jiao] + "角";
      if (fen > 0) outZ += zcfg.digitChars[fen] + "分";
      if (jiao === 0 && fen === 0) outZ += "整";
    } else {
      outZ += "整";
    }
    return parsed.neg ? zcfg.negWord + outZ : outZ;
  }

  // ---------------------------------------------------------------
  // 9. 모드별 스타일 옵션 정의 + 한 줄 처리 디스패처
  // ---------------------------------------------------------------

  var STYLE_OPTIONS = {
    cardinal: {
      ko: [["sino", T.style_cardinal_sino], ["native", T.style_cardinal_native], ["formal", T.style_cardinal_formal], ["all", T.style_cardinal_all]],
      en: [["words", T.style_cardinal_words]],
      ja: [["standard", T.style_cardinal_standard], ["formal", T.style_cardinal_formaljp]],
      zh: [["lower", T.style_cardinal_lower], ["upper", T.style_cardinal_upper]],
    },
    ordinal: {
      ko: [["native", T.style_ordinal_native], ["sino", T.style_ordinal_sino], ["all", T.style_ordinal_all]],
      en: [["words", T.style_ordinal_words]],
      ja: [["prefix", T.style_ordinal_prefix], ["suffix", T.style_ordinal_suffix]],
      zh: [["prefix", T.style_ordinal_prefix]],
    },
    digits: { ko: [["std", "-"]], en: [["std", "-"]], ja: [["std", "-"]], zh: [["std", "-"]] },
    time: {
      ko: [["civilian", T.style_time_civilian], ["24h", T.style_time_24h]],
      en: [["civilian", T.style_time_civilian], ["24h", T.style_time_24h]],
      ja: [["civilian", T.style_time_civilian], ["24h", T.style_time_24h]],
      zh: [["civilian", T.style_time_civilian], ["24h", T.style_time_24h]],
    },
    date: { ko: [["std", "-"]], en: [["std", "-"]], ja: [["std", "-"]], zh: [["std", "-"]] },
    currency: {
      ko: [["sino", T.style_currency_sino], ["formal", T.style_currency_formal]],
      en: [["words", T.style_currency_words]],
      ja: [["sino", T.style_currency_sino], ["formal", T.style_currency_formal]],
      zh: [["lower", T.style_currency_lower], ["upper", T.style_currency_upper]],
    },
  };

  var MODES_WITH_STYLE = { cardinal: 1, ordinal: 1, time: 1, currency: 1 };

  function cardinalLine(raw, lang, style) {
    if (lang === "ko") {
      if (style === "all") {
        var sino = groupedCardinal(raw, KO_SINO);
        if (sino === null) return null;
        var parsedAll = parseSignedDecimal(raw);
        var nativeWord = (!parsedAll.neg && !parsedAll.decPart && parseInt(parsedAll.intPart, 10) <= 99)
          ? koNativeCardinal(parseInt(parsedAll.intPart, 10)) : null;
        var formal = groupedCardinal(raw, KO_FORMAL);
        var out = "한자어 " + sino + " · 갖은자 " + formal;
        if (nativeWord) out = "고유어 " + nativeWord + " · " + out;
        return out;
      }
      if (style === "native") {
        var parsedN = parseSignedDecimal(raw);
        if (!parsedN) return null;
        if (!parsedN.neg && !parsedN.decPart && parseInt(parsedN.intPart, 10) <= 99) {
          return koNativeCardinal(parseInt(parsedN.intPart, 10));
        }
        // 고유어 표기 범위를 벗어나면 한자어로 대체하고 안내를 덧붙인다
        var sinoFallbackC = groupedCardinal(raw, KO_SINO);
        return sinoFallbackC === null ? null : sinoFallbackC + " (고유어는 0~99 정수만 지원)";
      }
      return groupedCardinal(raw, style === "formal" ? KO_FORMAL : KO_SINO);
    }
    if (lang === "en") return enCardinal(raw);
    if (lang === "ja") return groupedCardinal(raw, style === "formal" ? JA_FORMAL : JA_STD);
    return groupedCardinal(raw, style === "upper" ? ZH_UPPER : ZH_LOWER); // zh
  }

  function ordinalLine(raw, lang, style) {
    var s = raw.trim();
    if (!/^\d+$/.test(s)) return null;
    var n = parseInt(s, 10);
    if (lang === "ko") {
      if (style === "all") {
        var sino = koSinoOrdinal(n);
        var native = koNativeOrdinal(n);
        if (!sino) return null;
        return native ? ("고유어 " + native + " · 한자어 " + sino) : ("한자어 " + sino + " (고유어는 1~99만 지원)");
      }
      if (style === "native") {
        var nat = koNativeOrdinal(n);
        if (nat) return nat;
        var sinoFallback = koSinoOrdinal(n);
        return sinoFallback === null ? null : sinoFallback + " (고유어는 1~99만 지원)";
      }
      return koSinoOrdinal(n);
    }
    if (lang === "en") return enOrdinal(s);
    if (lang === "ja") {
      var kanji = convertGroupedInteger(s, JA_STD);
      if (kanji === null) return null;
      return style === "suffix" ? kanji + "番目" : "第" + kanji;
    }
    var zhKanji = convertGroupedInteger(s, ZH_LOWER);
    return zhKanji === null ? null : "第" + zhKanji; // zh
  }

  function processLine(raw, mode, lang, style) {
    if (mode === "cardinal") return cardinalLine(raw, lang, style);
    if (mode === "ordinal") return ordinalLine(raw, lang, style);
    if (mode === "digits") return digitsLine(raw, lang);
    if (mode === "time") return timeLine(raw, lang, style);
    if (mode === "date") return dateLine(raw, lang);
    if (mode === "currency") return currencyLine(raw, lang, style);
    return null;
  }

  // ---------------------------------------------------------------
  // 10. 샘플 데이터(모드별)
  // ---------------------------------------------------------------

  var SAMPLES = {
    cardinal: "1234567890\n-42\n3.14\n100000000\n0",
    ordinal: "1\n2\n3\n21\n100",
    digits: "010-1234-5678\n110\n123-456-7890",
    time: "9:05\n14:30\n23:59",
    date: "2026-09-30\n2000-01-01\n1999-12-31",
    currency: "12345\n1000000\n99.99",
  };

  // ---------------------------------------------------------------
  // 11. DOM 연결 및 UI 로직
  // ---------------------------------------------------------------

  var els = {
    input: document.getElementById("num-input"),
    status: document.getElementById("num-status"),
    statusTop: document.getElementById("num-status-top"),
    errorDetail: document.getElementById("num-error-detail"),
    errorDetailTop: document.getElementById("num-error-detail-top"),
    output: document.getElementById("num-output"),
    gutter: document.getElementById("num-gutter"),
    gutterInner: document.getElementById("num-gutter-inner"),
    outputGutter: document.getElementById("num-output-gutter"),
    outputGutterInner: document.getElementById("num-output-gutter-inner"),
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
    modeSelect: document.getElementById("num-mode-select"),
    styleSelect: document.getElementById("num-style-select"),
    styleLabelWrap: document.getElementById("num-style-label-wrap"),
  };

  if (!els.input) return; // 이 페이지가 아니면 아무 것도 하지 않음

  var state = { outputText: "", isValid: false, debounceTimer: null };

  function getMode() { return els.modeSelect ? els.modeSelect.value : "cardinal"; }
  function getStyle() { return els.styleSelect ? els.styleSelect.value : "std"; }

  function populateStyleOptions() {
    if (!els.styleSelect) return;
    var mode = getMode();
    var hasStyle = !!MODES_WITH_STYLE[mode];
    if (els.styleLabelWrap) els.styleLabelWrap.style.display = hasStyle ? "" : "none";
    els.styleSelect.style.display = hasStyle ? "" : "none";
    if (!hasStyle) return;
    var opts = (STYLE_OPTIONS[mode] && STYLE_OPTIONS[mode][LANG]) || [];
    var current = els.styleSelect.value;
    els.styleSelect.innerHTML = opts.map(function (o) {
      return '<option value="' + o[0] + '">' + escapeHtml(o[1]) + "</option>";
    }).join("");
    // 언어를 비교하는 스타일(고유어/all 등)이 있으면 기본값으로 그걸 우선 선택
    var hasPrev = opts.some(function (o) { return o[0] === current; });
    if (hasPrev) els.styleSelect.value = current;
    else if (opts.length) els.styleSelect.value = opts[0][0];
  }

  function updatePlaceholder() {
    var mode = getMode();
    var key = "placeholder_" + mode;
    if (T[key]) els.input.placeholder = T[key];
  }

  function escapeAndMark(text, ok) {
    return '<span class="' + (ok ? "num-line-ok" : "num-line-error") + '">' + escapeHtml(text) + "</span>";
  }

  function renderOutputGutter(lineCount) {
    if (!els.outputGutterInner) return;
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
  });
  if (els.output) {
    els.output.addEventListener("scroll", function () {
      if (els.outputGutterInner) els.outputGutterInner.style.transform = "translateY(-" + els.output.scrollTop + "px)";
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
  }

  function setToolbarEnabled(enabled) {
    [els.btnCopy, els.btnDownload].forEach(function (el) { if (el) el.disabled = !enabled; });
  }

  function renderPlaceholder() {
    els.output.innerHTML = '<p class="jf-placeholder">' + escapeHtml(T.outputPlaceholder) + "</p>";
    renderOutputGutter(1);
  }

  function process() {
    var text = els.input.value;
    renderGutter(text);

    if (text.trim() === "") {
      state.isValid = false;
      state.outputText = "";
      setStatus("idle", T.statusIdleText, T.statusIdleTop);
      renderPlaceholder();
      setToolbarEnabled(false);
      return;
    }

    var mode = getMode(), style = getStyle();
    var lines = text.split("\n");
    var htmlLines = [];
    var plainLines = [];
    var okCount = 0, totalCount = 0;

    lines.forEach(function (line) {
      if (line.trim() === "") { htmlLines.push(""); plainLines.push(""); return; }
      totalCount++;
      var result;
      try {
        result = processLine(line, mode, LANG, style);
      } catch (e) {
        result = null;
      }
      if (result === null || result === undefined) {
        htmlLines.push(escapeAndMark(T.lineError + " (" + line.trim() + ")", false));
        plainLines.push(T.lineError + " (" + line.trim() + ")");
      } else {
        okCount++;
        htmlLines.push(escapeAndMark(result, true));
        plainLines.push(result);
      }
    });

    state.isValid = true;
    state.outputText = plainLines.join("\n");
    els.output.innerHTML = '<pre class="num-output-text">' + htmlLines.join("\n") + "</pre>";
    renderOutputGutter(lines.length);
    setToolbarEnabled(true);

    if (totalCount > 0 && okCount === totalCount) {
      setStatus("valid", T.statusValidText, T.statusValidTop);
    } else if (okCount > 0) {
      setStatus("valid", T.statusPartialText, T.statusPartialTop);
    } else {
      setStatus("invalid", T.statusPartialText, T.statusPartialTop);
    }
  }

  function scheduleProcess() {
    clearTimeout(state.debounceTimer);
    state.debounceTimer = setTimeout(process, 250);
  }

  // ---------------------------------------------------------------
  // 12. 이벤트 연결
  // ---------------------------------------------------------------

  els.input.addEventListener("input", scheduleProcess);

  if (els.btnFormat) {
    els.btnFormat.addEventListener("click", function () {
      clearTimeout(state.debounceTimer);
      process();
      if (state.isValid) switchTab("output");
    });
  }

  if (els.btnSample) {
    els.btnSample.addEventListener("click", function () {
      els.input.value = SAMPLES[getMode()] || SAMPLES.cardinal;
      process();
    });
  }

  if (els.btnClear) {
    els.btnClear.addEventListener("click", function () {
      els.input.value = "";
      els.input.focus();
      process();
    });
  }

  if (els.modeSelect) {
    els.modeSelect.addEventListener("change", function () {
      populateStyleOptions();
      updatePlaceholder();
      process();
    });
  }
  if (els.styleSelect) {
    els.styleSelect.addEventListener("change", process);
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text);
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); } catch (e) { /* noop */ }
    document.body.removeChild(ta);
    return Promise.resolve();
  }

  function flashButton(btn, tempLabel) {
    var original = btn.textContent;
    btn.textContent = tempLabel;
    setTimeout(function () { btn.textContent = original; }, 1200);
  }

  if (els.btnCopy) {
    els.btnCopy.addEventListener("click", function () {
      if (!state.isValid) return;
      copyToClipboard(state.outputText);
      flashButton(els.btnCopy, T.copied);
    });
  }

  if (els.btnDownload) {
    els.btnDownload.addEventListener("click", function () {
      if (!state.isValid) return;
      var blob = new Blob([state.outputText], { type: "text/plain" });
      var url = URL.createObjectURL(blob);
      var a = document.createElement("a");
      a.href = url;
      a.download = "numbers.txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  function switchTab(tab) {
    var showInput = tab === "input";
    els.tabInput.classList.toggle("is-active", showInput);
    els.tabOutput.classList.toggle("is-active", !showInput);
    els.tabInput.setAttribute("aria-selected", String(showInput));
    els.tabOutput.setAttribute("aria-selected", String(!showInput));
    els.panelInput.hidden = !showInput;
    els.panelOutput.hidden = showInput;
  }
  els.tabInput.addEventListener("click", function () { switchTab("input"); });
  els.tabOutput.addEventListener("click", function () { switchTab("output"); });

  // ---------------------------------------------------------------
  // 13. 초기화
  // ---------------------------------------------------------------

  populateStyleOptions();
  updatePlaceholder();
  els.input.value = SAMPLES.cardinal;
  setToolbarEnabled(false);
  process();
})();
