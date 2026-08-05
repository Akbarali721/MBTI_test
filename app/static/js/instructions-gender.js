(function () {
  const form = document.getElementById("start-form");
  if (!form) return;

  const startBtn = document.getElementById("start-btn");
  const inputs = form.querySelectorAll('input[name="gender"]');
  const body = document.body;

  function syncTheme() {
    const checked = form.querySelector('input[name="gender"]:checked');
    body.classList.remove("theme-male", "theme-female");
    if (checked) {
      body.classList.add(checked.value === "female" ? "theme-female" : "theme-male");
      if (startBtn) startBtn.disabled = false;
    } else if (startBtn) {
      startBtn.disabled = true;
    }
  }

  inputs.forEach((input) => {
    input.addEventListener("change", syncTheme);
  });

  syncTheme();
})();
