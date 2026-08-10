(function () {
  var tg = window.Telegram && window.Telegram.WebApp;
  if (!tg || !tg.initData) {
    return;
  }
  try {
    tg.ready();
    tg.expand();
  } catch (_e) {
    /* optional */
  }
  var body = new URLSearchParams();
  body.set("init_data", tg.initData);
  fetch("/personality/telegram-bind", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString(),
    credentials: "same-origin",
  }).catch(function () {
    /* binding is best-effort; test flow works without it */
  });
})();
