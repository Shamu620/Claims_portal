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

      // Only block a click that would reload the exact page you're already on.
      // Reports&Analysis is active on all three report pages, so it must stay
      // clickable to jump back to Underwriter Performance from Claims Data/Trends.
      document.querySelectorAll('#main-nav-bar a').forEach((navLink) => {
        navLink.addEventListener('click', (e) => {
          const rawHref = navLink.getAttribute('href');
          if (!rawHref || rawHref === '#') return;

          const target = new URL(navLink.href, window.location.origin);
          if (target.pathname === window.location.pathname) {
            e.preventDefault();
          }
        });
      });

      const avatar = $('#user-avatar');
        const avatarPopup = $('#avatar-popup');
        let hideTimeout;

        avatar.on('click', function() {
          clearTimeout(hideTimeout);
          avatarPopup.fadeIn(150);
        });

        avatarPopup.on('mouseleave', function() {
          hideTimeout = setTimeout(function() {
            avatarPopup.fadeOut(150);
          }, 200); // small delay to let user move cursor into the popup
        });
      
      $.ajax({
        url: '/api/get-user-name-initials/',
        method: 'POST',
        headers: {
          "X-CSRFToken": getCookie('csrftoken')
        },
        success: function(response){
          $('#user-name-initials').text(response.name_initials);
          $('#user-role').text(response.role);
        },
        error: function(xhr){
          console.log(xhr.responseText);
        }

      })

      // ---- Settings panel (toggle, out of flow, no layout shift) ----
      const settingsLink = document.getElementById('settings');
      let settingsPanel = null;

      function openSettingsPanel() {
        settingsPanel = document.createElement('div');
        settingsPanel.className = 'settings-panel';
        settingsPanel.id = 'settings-panel';

        const changePwdBtn = document.createElement('button');
        changePwdBtn.className ='settings-panel-btn';
        changePwdBtn.textContent = 'Change Password';
        changePwdBtn.id = 'change-pwd-btn';
        settingsPanel.append(changePwdBtn);

        settingsLink.after(settingsPanel);
        settingsLink.setAttribute('aria-expanded', 'true');

        //listen to the change-password button
        changePwdBtn.addEventListener('click', function(){
          window.location.href = '/change-password/';
        })

      }

      function closeSettingsPanel() {
        if (!settingsPanel) return;
        settingsPanel.remove();
        settingsPanel = null;
        settingsLink.setAttribute('aria-expanded', 'false');
      }

      settingsLink.addEventListener('click', function (e) {
        e.preventDefault(); // stop href="#" from changing the URL
        e.stopPropagation(); // don't let the outside-click handler close it immediately
        if (settingsPanel) {
          closeSettingsPanel();
        } else {
          openSettingsPanel();
        }
      });

      // Click outside closes the panel
      document.addEventListener('click', function (e) {
        if (settingsPanel && !settingsPanel.contains(e.target)) {
          closeSettingsPanel();
        }
      });

      // Escape closes the panel
      // document.addEventListener('keydown', function (e) {
      //   if (e.ctrlKey && e.key === 'k') {
      //     closeSettingsPanel();
      //   }
      // });