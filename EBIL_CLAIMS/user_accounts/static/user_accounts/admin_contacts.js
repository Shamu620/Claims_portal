const btn = document.getElementById("copy-btn");
      const email = document.getElementById("admin-email").textContent.trim();

      function done() {
        btn.textContent = "Copied!";
        btn.classList.add("copied");
        setTimeout(function () {
          btn.textContent = "Copy";
          btn.classList.remove("copied");
        }, 700);
      }

      btn.addEventListener("click", function () {
        if (navigator.clipboard && window.isSecureContext) {
          navigator.clipboard.writeText(email).then(done); //.then(done) means “once the copy has finished, run done()” (the Copied! message).
        } else {
          const t = document.createElement("textarea");
          t.value = email;
          document.body.appendChild(t);
          t.select();
          document.execCommand("copy");
          document.body.removeChild(t);
          done();
        }
      });