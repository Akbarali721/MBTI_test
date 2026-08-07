/**
 * Radio tanlovli formalar uchun yagona progressiv yaxshilash.
 *
 * Forma atributlari:
 *   data-choice-form          — skript shu formani boshqaradi
 *   data-enables="#tugma"     — tanlov bo'lmaguncha tugma bloklanadi
 *   data-selected-class="..." — tanlangan variant yorlig'iga qo'shiladigan sinf
 *   data-theme-target="body"  — mavzu preview'i (ixtiyoriy kengaytma)
 * Radio atributi:
 *   data-theme-class="..."    — shu variant tanlanganda qo'yiladigan mavzu sinfi
 *
 * JS ishlamasa forma baribir yuboriladi: tugma HTML'da bloklanmagan, radio'larda
 * required bor va server tomonda ham tekshiruv bor.
 */
(function () {
  function setup(form) {
    var inputs = form.querySelectorAll('input[type="radio"]');
    if (!inputs.length) return;

    var enablesSelector = form.getAttribute("data-enables");
    var target = enablesSelector ? document.querySelector(enablesSelector) : null;
    var selectedClass = form.getAttribute("data-selected-class");
    var themeTarget = form.getAttribute("data-theme-target") === "body" ? document.body : null;

    var themeClasses = [];
    Array.prototype.forEach.call(inputs, function (input) {
      var themeClass = input.getAttribute("data-theme-class");
      if (themeClass && themeClasses.indexOf(themeClass) === -1) {
        themeClasses.push(themeClass);
      }
    });

    function sync() {
      var checked = form.querySelector('input[type="radio"]:checked');

      if (selectedClass) {
        Array.prototype.forEach.call(inputs, function (input) {
          var label = input.closest("label");
          if (label) label.classList.toggle(selectedClass, input.checked);
        });
      }

      if (themeTarget && themeClasses.length) {
        themeClasses.forEach(function (name) {
          themeTarget.classList.remove(name);
        });
        var themeClass = checked && checked.getAttribute("data-theme-class");
        if (themeClass) themeTarget.classList.add(themeClass);
      }

      if (target) target.disabled = !checked;
    }

    Array.prototype.forEach.call(inputs, function (input) {
      input.addEventListener("change", sync);
    });

    sync();
  }

  Array.prototype.forEach.call(document.querySelectorAll("[data-choice-form]"), setup);
})();
