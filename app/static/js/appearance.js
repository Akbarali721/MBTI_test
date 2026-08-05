document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("appearance-form");
  if (!form) {
    return;
  }

  const options = form.querySelectorAll('input[name="appearance_theme"]');
  const submitButton = form.querySelector("[data-appearance-submit]");
  if (!submitButton) {
    return;
  }

  const syncButtonState = () => {
    const checked = form.querySelector('input[name="appearance_theme"]:checked');
    submitButton.disabled = !checked;
  };

  options.forEach((option) => {
    option.addEventListener("change", syncButtonState);
  });

  syncButtonState();

  form.addEventListener("submit", (event) => {
    const checked = form.querySelector('input[name="appearance_theme"]:checked');
    if (!checked) {
      event.preventDefault();
      submitButton.disabled = true;
    }
  });
});
