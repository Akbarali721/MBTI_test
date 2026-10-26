(function () {
  var root = document.querySelector("[data-user-feedback-form]");
  if (!root) return;

  var submitUrl = root.getAttribute("data-submit-url");
  var commentWrap = root.querySelector("[data-comment-wrap]");
  var commentEl = root.querySelector("[data-comment]");
  var submitBtn = root.querySelector("[data-submit]");
  var errorEl = root.querySelector("[data-error]");
  var section = document.getElementById("user-feedback");
  var selectedRating = null;

  function showCommentStep() {
    if (!commentWrap) return;
    commentWrap.hidden = false;
    commentWrap.classList.remove("is-hidden");
    if (submitBtn) submitBtn.disabled = false;
  }

  function setError(msg) {
    if (!errorEl) return;
    if (!msg) {
      errorEl.hidden = true;
      errorEl.classList.add("is-hidden");
      errorEl.textContent = "";
      return;
    }
    errorEl.textContent = msg;
    errorEl.hidden = false;
    errorEl.classList.remove("is-hidden");
  }

  root.querySelectorAll("[data-rating]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      selectedRating = btn.getAttribute("data-rating");
      root.querySelectorAll("[data-rating]").forEach(function (b) {
        var on = b === btn;
        b.classList.toggle("is-selected", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      showCommentStep();
      setError("");
    });
  });

  if (submitBtn) {
    submitBtn.addEventListener("click", function () {
      if (!selectedRating || !submitUrl) return;
      setError("");
      submitBtn.disabled = true;
      var payload = {
        rating: selectedRating,
        comment: commentEl ? commentEl.value.trim() : "",
      };
      fetch(submitUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(payload),
      })
        .then(function (res) {
          if (!res.ok) throw new Error("bad status");
          return res.json();
        })
        .then(function (data) {
          if (!data || !data.ok) throw new Error("not ok");
          if (!section) return;
          section.innerHTML =
            '<div class="mbti-user-feedback__success" role="status">' +
            '<p class="mbti-user-feedback__success-title">' +
            (data.success_title || "Rahmat! 💜") +
            "</p><p class="mbti-user-feedback__success-body">" +
            (data.success_body || "") +
            "</p></div>";
        })
        .catch(function () {
          submitBtn.disabled = false;
          setError(submitBtn.getAttribute("data-error-text") || "Yuborib bo‘lmadi.");
        });
    });
  }
})();
