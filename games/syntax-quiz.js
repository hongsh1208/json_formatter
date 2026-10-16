(function () {
  "use strict";

  function shuffle(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i];
      a[i] = a[j];
      a[j] = tmp;
    }
    return a;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var panel = document.getElementById("gq-panel");
    var dataEl = document.getElementById("gq-data");
    if (!panel || !dataEl) return;

    var quizData;
    try {
      quizData = JSON.parse(dataEl.textContent);
    } catch (e) {
      return;
    }

    var selectWrap = document.getElementById("gq-select");
    var quizWrap = document.getElementById("gq-quiz");
    var finishWrap = document.getElementById("gq-finish");
    var progressEl = document.getElementById("gq-progress");
    var scoreEl = document.getElementById("gq-score");
    var stemEl = document.getElementById("gq-stem");
    var choicesEl = document.getElementById("gq-choices");
    var feedbackEl = document.getElementById("gq-feedback");
    var feedbackLabelEl = document.getElementById("gq-feedback-label");
    var explainEl = document.getElementById("gq-explain");
    var nextBtn = document.getElementById("gq-btn-next");
    var finishTitleEl = document.getElementById("gq-finish-title");
    var finishSummaryEl = document.getElementById("gq-finish-summary");
    var retryBtn = document.getElementById("gq-btn-retry");
    var changeLangBtn = document.getElementById("gq-btn-change-lang");

    if (!selectWrap || !quizWrap || !finishWrap || !choicesEl) return;

    var progressTemplate = panel.getAttribute("data-progress-template") || "{current} / {total}";
    var scoreLabel = panel.getAttribute("data-score-label") || "";
    var correctLabel = panel.getAttribute("data-correct-label") || "";
    var incorrectLabel = panel.getAttribute("data-incorrect-label") || "";
    var explainLabel = panel.getAttribute("data-explain-label") || "";
    var btnNextText = panel.getAttribute("data-btn-next") || "";
    var btnChangeLangText = panel.getAttribute("data-btn-change-lang") || "";
    var finishTitleText = panel.getAttribute("data-finish-title") || "";
    var finishSummaryTemplate = panel.getAttribute("data-finish-summary") || "{score} / {total}";
    var btnRetryText = panel.getAttribute("data-btn-retry") || "";

    nextBtn.textContent = btnNextText;
    retryBtn.textContent = btnRetryText;
    changeLangBtn.textContent = btnChangeLangText;
    finishTitleEl.textContent = finishTitleText;

    var currentLang = null;
    var questions = [];
    var currentIndex = 0;
    var score = 0;
    var answered = false;

    function fillTemplate(tpl, values) {
      return tpl.replace(/\{(\w+)\}/g, function (m, key) {
        return key in values ? values[key] : m;
      });
    }

    function showQuestion() {
      answered = false;
      var q = questions[currentIndex];
      progressEl.textContent = fillTemplate(progressTemplate, { current: currentIndex + 1, total: questions.length });
      scoreEl.textContent = scoreLabel + ": " + score;
      stemEl.textContent = q.stem;
      choicesEl.innerHTML = "";
      feedbackEl.hidden = true;

      q.choices.forEach(function (choiceText, idx) {
        var btn = document.createElement("button");
        btn.type = "button";
        btn.className = "gq-choice-btn";
        btn.textContent = choiceText;
        btn.addEventListener("click", function () {
          onAnswer(idx, btn);
        });
        choicesEl.appendChild(btn);
      });
    }

    function onAnswer(idx, btnEl) {
      if (answered) return;
      answered = true;
      var q = questions[currentIndex];
      var isCorrect = idx === q.correct;
      if (isCorrect) score += 1;

      Array.prototype.forEach.call(choicesEl.children, function (btn, i) {
        btn.disabled = true;
        if (i === q.correct) btn.classList.add("is-correct");
        else if (i === idx) btn.classList.add("is-incorrect");
      });

      feedbackLabelEl.textContent = isCorrect ? correctLabel : incorrectLabel;
      feedbackLabelEl.className = "gq-feedback-label " + (isCorrect ? "is-correct" : "is-incorrect");
      explainEl.textContent = explainLabel ? explainLabel + ": " + q.explain : q.explain;
      feedbackEl.hidden = false;
      scoreEl.textContent = scoreLabel + ": " + score;
    }

    function showFinish() {
      quizWrap.hidden = true;
      finishWrap.hidden = false;
      finishSummaryEl.textContent = fillTemplate(finishSummaryTemplate, { score: score, total: questions.length });
    }

    function startQuiz(progLang) {
      currentLang = progLang;
      questions = shuffle(quizData[progLang] || []);
      currentIndex = 0;
      score = 0;
      selectWrap.hidden = true;
      finishWrap.hidden = true;
      quizWrap.hidden = false;
      if (questions.length) showQuestion();
    }

    Array.prototype.forEach.call(document.querySelectorAll("[data-quiz-lang]"), function (btn) {
      btn.addEventListener("click", function () {
        startQuiz(btn.getAttribute("data-quiz-lang"));
      });
    });

    nextBtn.addEventListener("click", function () {
      currentIndex += 1;
      if (currentIndex >= questions.length) {
        showFinish();
      } else {
        showQuestion();
      }
    });

    retryBtn.addEventListener("click", function () {
      if (currentLang) startQuiz(currentLang);
    });

    changeLangBtn.addEventListener("click", function () {
      finishWrap.hidden = true;
      quizWrap.hidden = true;
      selectWrap.hidden = false;
    });
  });
})();
