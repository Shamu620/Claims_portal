 const form = document.querySelector("form");
      const signInBtn = document.querySelector(".sign-in-btn");
      const viewPasswordBtn = document.querySelector("#view-password-btn");
      const passwordInput = document.querySelector("#password");

      if (form && signInBtn) {
        form.addEventListener("submit", function () {
          signInBtn.style.fontSize = "0.875rem";
          signInBtn.textContent = "Hold on a second... ↻";
          // Optional: disable the button to prevent double-submitting
          signInBtn.disabled = true;
        });
      }

      setTimeout(function () {
        const errorAlert = document.getElementById("error-alert");
        if (errorAlert) {
          errorAlert.style.transition = "opacity 0.5s ease";
          errorAlert.style.opacity = "0";
          setTimeout(() => errorAlert.remove(), 500);
        }
      }, 3000); // 3000 milliseconds = 3 seconds

      viewPasswordBtn.addEventListener("click", function () {
        if (passwordInput.type === "password") {
          passwordInput.type = "text";
          viewPasswordBtn.textContent = "🙈";
        } else {
          passwordInput.type = "password";
          viewPasswordBtn.textContent = "👁️";
        }
      });