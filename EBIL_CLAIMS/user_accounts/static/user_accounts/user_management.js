 const usersTable = $("#users-table");

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

      $(window).on("resize", function () {
        if ($.fn.DataTable.isDataTable(usersTable)) {
          usersTable.DataTable().columns.adjust().draw();
        }
      });

      async function initUsersTable() {
        try {
          const response = await fetch("/api/fetch-all-users/");

          if (!response.ok) {
            throw new Error("Failed to fetch users. Status: " + response.status);
            Swal.fire({
              title: 'Oops...!',
              icon: 'error',
              text: `Failed to fetch users. Status: ${response.status}`
            })
            
          } else {
            const res = await response.json();

            const data = res.data;
            const count_info = res.count_info;

            $("#count-total-users").text(count_info.total_users);
            $("#count-admins").text(count_info.admins_count);
            $("#count-subadmins").text(count_info.sub_admins_count);

            if ($.fn.DataTable.isDataTable(usersTable)) {
              // usersTable.DataTable().clear().destroy();
              $("#users-table").DataTable().destroy();
              $("#users-table").empty();
            }

            const table = usersTable.DataTable({
              serverSide: false,
              processing: true,
              layout: {
                topStart: "pageLength",
                topEnd: null,
                bottomStart: "info",
                bottomEnd: "paging",
              },
              scrollY: "46dvh",
              // scrollCollapse: true,
              autoWidth: false,
              paging: true,
              pageLength: 20,
              lengthMenu: [20, 20, 50, 100],
              data: data,
              columns: [
                { data: "user_id", title: "User Id" },
                { data: "name", title: "Name" },
                { data: "pf", title: "PF" },
                { data: "username", title: "Username" },
                { data: "email", title: "Email" },
                { data: "role", title: "Role" },
                { data: "date_joined", title: "Date Joined" },
                { data: "last_login", title: "Last Login" },
                {
                  data: null,
                  title: "Action",
                  render: function (data, type, row) {
                    return `<button type="button" class="btn-edit" data-pf="${row.pf}">Remove</button>`;
                  },
                },
              ],
              columnDefs: [
                { width: "5%", targets: 0 }, //User Id
                { width: "10%", targets: 1 }, //Name
                { width: "5%", targets: 2 }, //PF
                { width: "5%", targets: 3 }, //Username
                { width: "15%", targets: 4 }, //Email
                { width: "5%", targets: 5 }, //Role
                { width: "7%", targets: 6 }, //Date Joined
                { width: "10%", targets: 7 }, //Last Login
                { width: "7%", targets: 8 }, //Action
              ],
            });
            requestAnimationFrame(() => {
              table.columns.adjust().draw();
            });
            return table;
          }
        } catch (err) {
          Swal.fire({
            title: 'Oops...!',
            icon: 'error',
            text: `Error fetching users: ${err.message}`
          })
          console.error("Error fetching users:", err);
        }
      }

      function confirmUserSubmission(nameOfUser, role, userDataPayload, username) {
        $("#confirm-add-dialog")[0].showModal();
        $("#confirm-name").text(nameOfUser);
        $("#confirm-role").text(role);

        $("#confirm-add-user")
          .off("click")
          .on("click", function () {
            $.ajax({
              url: "/api/create-user/",
              method: "POST",
              headers: {
                "X-CSRFToken": getCookie("csrftoken"),
              },
              data: JSON.stringify(userDataPayload),
              contentType: "application/json",
              beforeSend: function () {
                $("#loading-dialog")[0].showModal();
              },
              success: function () {
                Swal.fire({
                  title: 'Success!',
                  icon: 'success',
                  text: `Successfully added ${nameOfUser} as ${username}!`
                })
                
                $("#add-user-form")[0].reset();
                $("#confirm-add-dialog")[0].close();
                $("#add_user_dialog")[0].close();
                $("#loading-dialog")[0].close();

                initUsersTable();
                // usersTable.DataTable().columns.adjust().draw();
                // if ($.fn.DataTable.isDataTable("#users-table")) {
                // $("#users-table").DataTable().ajax.reload(null, false);
                //  } //will not work because you did not initialize the datatable with $.ajax() Instead use: initUsersTable(); to redraw the table
              },
              error: function (xhr) {
                Swal.fire({
                  title: 'Oops...!',
                  icon: 'error',
                  text: `Failed to add ${nameOfUser} to the database. Error: ${JSON.parse(xhr.responseText)}`
                })
                
                console.log(xhr);
                $("#add-user-form")[0].reset();
                $("#confirm-add-dialog")[0].close();
                $("#loading-dialog")[0].close();
              },
              complete: function () {
                $("#add-user-form")[0].reset();
                $("#loading-dialog")[0].close();
                $("#confirm-add-dialog")[0].close();
                $("#loading-dialog")[0].close();
                userDataPayload = null;
                role = null;
                nameOfUser = null;
              },
            });
          });
      }

      const confirmAddDialog = $("#confirm-add-dialog")[0]; //cache this element to avoid DOM search every time the button is clicked
      const addUserDialog = $("#add_user_dialog")[0]; //cache this element to avoid DOM search every time the button is clicked

      $("#cancel-add-user, #dlg-cancel-btn, #dlg-x-close-btn, #cancel-x-add-user")
        .off("click")
        .on("click", function () {
          if (confirmAddDialog.open) {
            confirmAddDialog.close();
            $("#add-user-form")[0].reset();
          }
          if (addUserDialog.open) {
            addUserDialog.close();
            $("#add-user-form")[0].reset();
          }
        });

      function addUser() {
        const inputElements = [
          $("#anu-first-name"),
          $("#anu-last-name"),
          $("#anu-email-address"),
          $("#anu-password"),
          $("#anu-role"),
          $("#anu-pf"),
        ];

        $("#add-user-form").on("submit", function (e) {
          e.preventDefault();

          const form = $("#add-user-form")[0];

          if (!form.checkValidity()) {
            form.reportValidity();
            return;
          }
          const firstName = $("#anu-first-name").val().trim();
          const lastName = $("#anu-last-name").val().trim();

          let userDataPayload = {
            more_user_details: {},
          };
          let nameOfUser = `${$("#anu-first-name").val()} ${$("#anu-last-name").val()}`;
          let role = $("#anu-role").val();
          let username =
            firstName.charAt(0) + lastName.charAt(0) + $("#anu-pf").val();

          inputElements.forEach((input) => {
            if (input.attr("name")) {
              userDataPayload.more_user_details[input.attr("data-correct-db-name")] =
                input.val();
            } else {
              userDataPayload[input.attr("data-correct-db-name")] = input.val();
            }
          });

          confirmUserSubmission(nameOfUser, role, userDataPayload, username);

          userDataPayload = null;
          role = null;
          nameOfUser = null;
        });
      }

      $(document).ready(function () {
        initUsersTable();
        addUser();

        $("#search-users").on("input keydown keyup change", function () {
          const searchTerm = $(this).val();
          usersTable.DataTable().search(searchTerm).draw();
        });

        $("#role-filter").on("change", function () {
          const selectedRole = $(this).val();
          if (selectedRole) {
            usersTable
              .DataTable()
              .column(5)
              .search("^" + selectedRole + "$", true, false)
              .draw(); //^-start of the word, $- end of the word //regex (true) //fuzzing/smart (false) - exact name
          } else {
            usersTable.DataTable().column(5).search("").draw();
          }
        });

        $("#users-table").on("click", "tbody tr button", function () {
          const table = $("#users-table").DataTable();
          const row = table.row($(this).closest("tr"));
          const rowData = row.data();
          Swal.fire({
            title: "Confirm:",
            icon: "warning",
            text: `Are you sure you want to PERMANENTLY delete ${rowData.name} as ${rowData.role}?`,
            showCancelButton: true,
            confirmButtonText: "Yes",
            cancelButtonText: "No",
          }).then((result) => {
            if (result.isConfirmed) {
              const url = `/api/delete-user/${encodeURIComponent(rowData.user_id)}/${encodeURIComponent(rowData.pf)}/`;

              $.ajax({
                url: url,
                method: "DELETE",
                headers: {
                  "X-CSRFToken": getCookie("csrftoken"),
                },
                beforeSend: function () {
                  $("#loading-dialog")[0].showModal();
                },
                error: function (xhr) {
                  let errorMsg = "Unknown error";
                  try {
                    errorMsg = JSON.parse(xhr.responseText).error;
                  } catch (e) {
                    errorMsg = xhr.responseText;
                  }

                  Swal.fire({
                    title: "Oops...!",
                    icon: "error",
                    text: `Failed to delete ${rowData.name}. Error: ${errorMsg}`,
                  });
                  console.log(errorMsg);
                },
                success: function (response) {
                  Swal.fire({
                    title: "Success",
                    icon: "success",
                    text: response.success || `Successfully deleted ${rowData.name}`,
                  });

                  initUsersTable();
                },
                complete: function () {
                  $("#loading-dialog")[0].close();
                },
              });
            }
          });
        });

          $('#anu-view-password').on('click', function(){
            const passwordInput = $('#anu-password');
                
            if (passwordInput.prop('type') === 'password') {
              passwordInput.prop('type', 'text');
              $(this).text('🙈'); // Switch icon to hidden state
            } else {
              passwordInput.prop('type', 'password');
              $(this).text('👁️'); // Switch back to visible state
            }
        });

        const avatar = $('#header-avatar');
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
      
      });