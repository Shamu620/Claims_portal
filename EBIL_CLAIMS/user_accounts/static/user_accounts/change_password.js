const currentPassword = $("#old-password");
            const newPassword = $("#new-password");
            const confirmNewPassword = $("#confirm-password");
            const charNumber = $("#char_number");
            const notEntirelyNumbers = $("#not-numbers");
            const notCommonPwd = $("#not-common");
            const differCurrentPwd = $("#differ-current-pwd");
            const newMatchConfirm = $("#new-confirm-match");
            const inputWrap = $(".input-wrap");
            const changePwdForm = $("#change-password-form");

            newPassword.on("keydown keyup change", function () {
                if (newPassword.val().length >= 8) {
                    charNumber.addClass("green");
                } else {
                    charNumber.removeClass("green");
                }
                if (/[a-zA-Z]+/.test(newPassword.val())) {
                    notEntirelyNumbers.addClass("green");
                } else {
                    notEntirelyNumbers.removeClass("green");
                }
                // A small sample list of common passwords
                const commonPasswords = [
                    "password",
                    "123456",
                    "123456789",
                    "qwerty",
                    "admin",
                    "welcome",
                    "123123",
                ];
                if (
                    !commonPasswords.includes(newPassword.val()) &&
                    newPassword.val().length >= 8
                ) {
                    notCommonPwd.addClass("green");
                } else {
                    notCommonPwd.removeClass("green");
                }
                if (
                    currentPassword.val() != newPassword.val() &&
                    newPassword.val().length >= 8 &&
                    currentPassword.val().length > 0
                ) {
                    differCurrentPwd.addClass("green");
                } else {
                    differCurrentPwd.removeClass("green");
                }
            });

            confirmNewPassword.on("keyup keydown change", function () {
                if (confirmNewPassword.val() === newPassword.val()) {
                    newMatchConfirm.addClass("green");
                } else {
                    newMatchConfirm.removeClass("green");
                }
            });

            inputWrap.on("click", "button", function () {
                const closestInput = $(this).siblings("input");
                if (closestInput.attr("type") === "password") {
                    closestInput.attr("type", "text");
                    $(this).html("🙈");
                } else {
                    closestInput.attr("type", "password");
                    $(this).html(`
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#52607F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>
                    `);
                }
            });

            $(".rules-error-toast").fadeOut();

            changePwdForm.on("submit", function (event) {
                event.preventDefault();

                if (
                    newPassword.val().length < 8 ||
                    newPassword.val() == currentPassword.val() ||
                    confirmNewPassword.val() != newPassword.val()
                ) {
                    $(".rules-error-toast").fadeIn();
                    setTimeout(function () {
                        $(".rules-error-toast").fadeOut();
                    }, 2500);
                } else {
                    // Hide error toast and submit natively without causing an infinite loop
                    $(".rules-error-toast").fadeOut();
                    changePwdForm[0].submit();
                }
            });

            //         function getCookie(name) {
            //     let cookieValue = null;
            //     if (document.cookie && document.cookie !== "") {
            //       const cookies = document.cookie.split(";");
            //       for (let i = 0; i < cookies.length; i++) {
            //         const cookie = cookies[i].trim();
            //         if (cookie.substring(0, name.length + 1) === name + "=") {
            //           cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            //           break;
            //         }
            //       }
            //     }
            //     return cookieValue;
            //   }

            //         $.ajax({
            //             url: '...',
            //             method: 'POST',
            //             headers: {
            //                 'X-CSRFToken': getCookie('csrftoken')
            //             },

            //         })