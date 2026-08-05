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

  document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var id = btn.getAttribute("data-copy-target");
      var el = id ? document.getElementById(id) : null;
      if (!el) return;
      var text = (el.textContent || "").trim();
      if (!text || text === "—") return;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = "Nusxalandi";
          setTimeout(function () {
            btn.textContent = "Nusxalash";
          }, 2000);
        });
      }
    });
  });
})();
