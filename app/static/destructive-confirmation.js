(() => {
  const modalElement = document.getElementById("deleteConfirmationModal");
  const input = document.getElementById("deleteConfirmationInput");
  const submitButton = document.getElementById("deleteConfirmationSubmit");
  const message = document.getElementById("deleteConfirmationMessage");
  if (!modalElement || !input || !submitButton || !message || !window.bootstrap) return;

  const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
  let pendingForm = null;

  const setConfirmation = (form, subject) => {
    pendingForm = form;
    input.value = "";
    submitButton.disabled = true;
    message.textContent = form.dataset.deleteMessage || `Permanently delete ${subject}? This action cannot be undone.`;
    modal.show();
  };

  document.querySelectorAll("form[data-delete-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (form.dataset.deleteConfirmed === "true") return;
      event.preventDefault();
      setConfirmation(form, form.dataset.deleteSubject || "this record");
    });
  });

  document.querySelectorAll("form[data-bulk-delete-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const action = form.querySelector('[name="action"]')?.value;
      if (action !== "delete" || form.dataset.deleteConfirmed === "true") return;
      event.preventDefault();
      const selected = form.querySelectorAll('[name="user_ids"]:checked').length;
      setConfirmation(form, `${selected} selected user account${selected === 1 ? "" : "s"}`);
    });
  });

  input.addEventListener("input", () => {
    submitButton.disabled = input.value !== "delete";
  });

  submitButton.addEventListener("click", () => {
    if (!pendingForm || input.value !== "delete") return;
    let confirmation = pendingForm.querySelector('input[name="delete_confirmation"]');
    if (!confirmation) {
      confirmation = document.createElement("input");
      confirmation.type = "hidden";
      confirmation.name = "delete_confirmation";
      pendingForm.appendChild(confirmation);
    }
    confirmation.value = input.value;
    pendingForm.dataset.deleteConfirmed = "true";
    submitButton.disabled = true;
    pendingForm.requestSubmit();
  });

  modalElement.addEventListener("shown.bs.modal", () => input.focus());
  modalElement.addEventListener("hidden.bs.modal", () => {
    pendingForm = null;
    input.value = "";
    submitButton.disabled = true;
  });
})();
