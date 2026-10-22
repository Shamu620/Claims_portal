let emailInput = null;


      function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }  

    $('#form-email').on('submit', function(e){
      e.preventDefault();
      emailInput = $('#input-email').val().trim();
      const displayEmail = $('#display-email');

      $.ajax({
        url: '/recover-password/',
        method: 'POST',
        headers: {"X-CSRFToken": getCookie("csrftoken")},
        data: JSON.stringify({
          email: emailInput  //Most APIs expect an object:
        }),
        contentType: 'application/json',
        beforeSend: function(){
          $('#loading-dialog')[0].showModal();
        },
        error: function(xhr){
          Swal.fire({
            title: 'Oops...!',
            icon: 'error',
            text: `Failed! [${xhr.responseText}]`
          })
        },
        success: function(){
          $('#card-email').prop('hidden', true);
          $('#card-code').prop('hidden', false);
          displayEmail.text(emailInput);
        },
        complete: function(){
          $('#loading-dialog')[0].close();
        }  
      })

    })

    $('#form-code').on('submit', function(e){
      e.preventDefault();

      const verificationCode = $('#verification-code').val().trim();

      $.ajax({
        url: '/api/confirm-otp/',
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        data: JSON.stringify({ 
          verification_code: verificationCode,
          email: emailInput
        }),
        contentType: 'application/json',
        beforeSend: function(){
          $('#loading-dialog')[0].showModal();
        },
        error: function(xhr){
          // Swal.fire({
          //   title: 'Oops...!',
          //   icon: 'error',
          //   text: `Failed! [${xhr.responseText}]`
          // });
          $('#card-email').prop('hidden', true);
          $('#card-code').prop('hidden', true);
          $('#card-failure').prop('hidden', false);
          console.log("Failed: " + xhr.responseText);
        },
        success: function(){
          $('#card-email').prop('hidden', true);
          $('#card-code').prop('hidden', true);
          $('#card-success').prop('hidden', false);
        },
        complete: function(){
          $('#loading-dialog')[0].close();
          emailInput = null;
        } 
      })
    })