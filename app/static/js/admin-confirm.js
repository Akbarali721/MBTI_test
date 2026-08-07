// CSP "script-src 'self'" inline onsubmit'ni bloklaydi, shuning uchun tasdiq
// so'rovi data-confirm atributi orqali shu yerda ulanadi.
(function () {
  "use strict";

  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (!form || !form.matches("form[data-confirm]")) {
      return;
    }
    var message = form.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  });
})();
