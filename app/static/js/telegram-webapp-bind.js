(function () {
  var MAX_SDK_WAIT_MS = 3000;
  var MAX_BIND_ATTEMPTS = 6;
  var RETRY_DELAY_MS = 250;

  function postBind(initData, attempt, done) {
    var body = new URLSearchParams();
    body.set("init_data", initData);
    fetch("/personality/telegram-bind", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
      credentials: "same-origin",
    })
      .then(function (response) {
        return response.json().catch(function () {
          return { ok: false, reason: "bad_response" };
        });
      })
      .then(function (payload) {
        if (payload && payload.ok) {
          done(true);
          return;
        }
        var reason = payload && payload.reason;
        if (reason === "no_session" && attempt + 1 < MAX_BIND_ATTEMPTS) {
          window.setTimeout(function () {
            postBind(initData, attempt + 1, done);
          }, RETRY_DELAY_MS * (attempt + 1));
          return;
        }
        done(false);
      })
      .catch(function () {
        if (attempt + 1 < MAX_BIND_ATTEMPTS) {
          window.setTimeout(function () {
            postBind(initData, attempt + 1, done);
          }, RETRY_DELAY_MS * (attempt + 1));
          return;
        }
        done(false);
      });
  }

  function tryBind(attempt, startedAt) {
    var tg = window.Telegram && window.Telegram.WebApp;
    if (!tg) {
      if (Date.now() - startedAt < MAX_SDK_WAIT_MS) {
        window.setTimeout(function () {
          tryBind(attempt, startedAt);
        }, 100);
      }
      return;
    }
    try {
      tg.ready();
      tg.expand();
    } catch (_e) {
      /* optional */
    }
    var initData = tg.initData;
    if (!initData) {
      return;
    }
    postBind(initData, 0, function () {
      /* best-effort */
    });
  }

  function start() {
    tryBind(0, Date.now());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
