(function () {
  const form = document.getElementById("answer-form");
  if (!form) return;

  const button = document.getElementById("next-question-button");
  const options = form.querySelectorAll(".mbti-option");
  const inputs = form.querySelectorAll('input[type="radio"]');

  function updateSelection() {
    options.forEach((option) => {
      const input = option.querySelector('input[type="radio"]');
      if (input) {
        option.classList.toggle("is-selected", input.checked);
      }
    });

    if (button) {
      button.disabled = !form.querySelector('input[type="radio"]:checked');
    }
  }

  inputs.forEach((input) => {
    input.addEventListener("change", updateSelection);
  });

  updateSelection();
})();
