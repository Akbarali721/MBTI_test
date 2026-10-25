(function () {
  var root = document.getElementById("growth-focus");
  if (!root) return;

  var weekEl = document.getElementById("growth-week-data");
  var weekById = weekEl ? JSON.parse(weekEl.textContent || "{}") : null;
  var weekPlanRoot = document.getElementById("week-plan");

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
    }
  });
})();
