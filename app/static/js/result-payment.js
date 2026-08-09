/**
 * To'lov modali va nusxalash tugmalari.
 * Matnlar shablondan data-* atributlari orqali keladi (i18n katalogi).
 */
(function () {
  var dialog = document.getElementById("payment-modal");
  var openBtn = document.getElementById("open-payment-modal");
  var closeBtn = document.getElementById("close-payment-modal");

  if (openBtn && dialog) {
    openBtn.addEventListener("click", function () {
      if (typeof dialog.showModal === "function") {
        dialog.showModal();
      } else {
        dialog.setAttribute("open", "open");
      }
    });
  }

  if (closeBtn && dialog) {
    closeBtn.addEventListener("click", function () {
      if (typeof dialog.close === "function") {
        dialog.close();
      } else {
        dialog.removeAttribute("open");
      }
    });
  }

  function label(btn, name, fallback) {
    return btn.getAttribute(name) || fallback;
  }

  function flash(btn, text) {
    btn.textContent = text;
    setTimeout(function () {
      btn.textContent = label(btn, "data-copy-label", text);
    }, 2000);
  }

  /** navigator.clipboard faqat xavfsiz kontekstda bor — zaxira sifatida execCommand. */
  function legacyCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.top = "-1000px";
    area.style.opacity = "0";
    document.body.appendChild(area);
    var copied = false;
    try {
      area.select();
      area.setSelectionRange(0, text.length);
      copied = document.execCommand("copy");
    } catch (error) {
      copied = false;
    }
    document.body.removeChild(area);
    return copied;
  }

  function copyText(btn, text) {
    var okLabel = label(btn, "data-copied-label", "OK");
    var failLabel = label(btn, "data-copy-failed-label", okLabel);

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () {
          flash(btn, okLabel);
        },
        function () {
          flash(btn, legacyCopy(text) ? okLabel : failLabel);
        }
      );
      return;
    }
    flash(btn, legacyCopy(text) ? okLabel : failLabel);
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-copy-target]"), function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-copy-target");
      var el = id ? document.getElementById(id) : null;
      if (!el) return;
      var text = (el.textContent || "").trim();
      if (!text || text === "—") return;
      copyText(btn, text);
    });
  });
})();
