/**
 * Natija tayyorlanayotganda xabarlarni almashtirib turadi va natija sahifasiga o'tadi.
 * Matnlar shablondan data-loading-steps orqali keladi (i18n katalogi).
 * JS ishlamasa <noscript> ichidagi meta refresh va havola ishlaydi.
 */
(function () {
  var el = document.getElementById("loading-message");
  if (!el) return;

  var resultUrl = el.getAttribute("data-result-url");
  var messages;
  try {
    messages = JSON.parse(el.getAttribute("data-loading-steps") || "[]");
  } catch (error) {
    messages = [];
  }

  var index = 0;
  var interval = null;
  if (messages.length > 1) {
    interval = setInterval(function () {
      index = (index + 1) % messages.length;
      el.textContent = messages[index];
    }, 650);
  }

  setTimeout(function () {
    if (interval) clearInterval(interval);
    if (resultUrl) window.location.href = resultUrl;
  }, 2000);
})();
