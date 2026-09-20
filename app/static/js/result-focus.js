(function () {
  var root = document.getElementById("growth-focus");
  var card = document.getElementById("today-card");
  if (!root || !card) return;

  var todayEl = document.getElementById("growth-today-data");
  var weekEl = document.getElementById("growth-week-data");
  var todayById = todayEl ? JSON.parse(todayEl.textContent || "{}") : {};
  var weekById = weekEl ? JSON.parse(weekEl.textContent || "{}") : null;
  var weekPlanRoot = document.getElementById("week-plan");

  function setText(field, value) {
    var node = card.querySelector('[data-field="' + field + '"]');
    if (node) node.textContent = value || "";
  }

  function renderSteps(steps) {
    var list = card.querySelector('[data-field="steps"]');
    if (!list) return;
    list.innerHTML = "";
    (steps || []).forEach(function (step) {
      var li = document.createElement("li");
      li.textContent = step;
      list.appendChild(li);
    });
  }

  function renderToday(id) {
    var data = todayById[id];
    if (!data) return;
    setText("area_name", data.area_name);
    setText("situation", data.situation);
    setText("method", data.method);
    renderSteps(data.steps);
    setText("success_criteria", data.success_criteria);
    setText("lighter_variant", data.lighter_variant);
    setText("check_question", data.check_question);
    var task = card.querySelector(".mbti-today-card__task");
    if (task) task.innerHTML = "<strong>" + (data.today_task || "") + "</strong>";
    card.hidden = false;
  }

  function renderWeek(id) {
    if (!weekPlanRoot || !weekById) return;
    var days = weekById[id];
    if (!days) return;
    var list = weekPlanRoot.querySelector(".mbti-week-plan__list");
    if (!list) return;
    list.innerHTML = "";
    days.forEach(function (day) {
      var li = document.createElement("li");
      li.className = "mbti-week-plan__item";
      li.innerHTML =
        '<p class="mbti-week-plan__day">' +
        day.day +
        "-kun</p><p class=\"mbti-week-plan__task\">" +
        day.task +
        '</p><p class="mbti-week-plan__meta">' +
        day.minutes +
        " · " +
        day.success +
        "</p>";
      list.appendChild(li);
    });
    weekPlanRoot.hidden = false;
  }

  function setActive(id) {
    root.querySelectorAll("[data-growth-focus]").forEach(function (btn) {
      btn.classList.toggle("is-active", btn.getAttribute("data-growth-focus") === id);
    });
    root.querySelectorAll("[data-growth-panel]").forEach(function (panel) {
      panel.classList.toggle("is-hidden", panel.getAttribute("data-growth-panel") !== id);
    });
    renderToday(id);
    renderWeek(id);
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("focus", id);
      window.history.replaceState({}, "", url.toString());
    } catch (e) {
      /* ignore */
    }
  }

  root.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-growth-focus]");
    if (btn) {
      setActive(btn.getAttribute("data-growth-focus"));
      return;
    }
    if (event.target.closest("[data-growth-dismiss]")) {
      card.hidden = true;
      root.querySelectorAll("[data-growth-focus]").forEach(function (b) {
        b.classList.remove("is-active");
      });
      root.querySelectorAll("[data-growth-panel]").forEach(function (p) {
        p.classList.add("is-hidden");
      });
      try {
        var url = new URL(window.location.href);
        url.searchParams.delete("focus");
        window.history.replaceState({}, "", url.toString());
      } catch (e2) {
        /* ignore */
      }
    }
  });
})();
