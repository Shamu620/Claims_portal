const dialog = document.getElementById("claim-details-dialog");
  const form = document.getElementById("details-form");
  const inputs = form.querySelectorAll("input, select, textarea");
  const editBtn = document.getElementById("edit-btn");
  const cancelEditing = document.getElementById("cancel-editing-btn");
  const closeDialogBtn = document.getElementById("close-dialog-btn");
  const saveBtn = document.getElementById("save-btn");
  const container = document.getElementById("confirm-dialog-items");
  const cancelConfirmBtn = document.getElementById("cancel-confirm-btn");
  const confirmChangesBtn = document.getElementById("confirm-changes-btn");
  const confirmDialog = document.getElementById("confirm-dialog");
  const addNewClaimBtn = document.getElementById('add-new-claim-btn');
  const submitNewClaimBtn = document.getElementById('submit-new-claim-btn');
  const addNewClaimStatus = document.getElementById('add-new-claim-status');
  const addNewClaimSubStatus = document.getElementById('add-new-claim-sub-status');
  const ancDialog = document.getElementById('add-new-claim-dialog');
  const ancForm = document.getElementById('add-new-claim-form');
  const ancCancelDialogBtn = document.getElementById('add-new-claim-close-btn');
  const addNewClaimDocumented = document.getElementById('add-new-claim-documented');
  const addNewClaimDateFullyDocumented = document.getElementById('add-new-claim-date-fully-documented');
  const addNewClaimClosureDate = document.getElementById('add-new-claim-closure-date');
  const addNewClaimDvAmount = document.getElementById('add-new-claim-dv-amount');
  const addNewClaimDateDvIssued = document.getElementById('add-new-claim-date-dv-issued');
  const addNewClaimDateDvReturned = document.getElementById('add-new-claim-date-dv-returned');
  const addNewClaimAmountPaid = document.getElementById('add-new-claim-amount-paid');
  let postPayload = null;
  const elementIds = [
    "claim-id",
    "cover-type-header",
    "name-of-insured",
    "claim-number",
    "days-pending",
    "category",
    "cover-type",
    "circumstance",
    "intimation-date",
    "date-of-loss",
    "documented",
    "date-fully-documented",
    "doc-link-1",
    "doc-link-2",
    "underwriter",
    "branch",
    "handler",
    "status",
    "sub-status",
    "notes",
    "sum-insured",
    "dv-amount",
    "date-dv-issued",
    "date-dv-returned",
    "closure-date",
    "last-updated",
    "amount-paid",
  ];

  const elements = {};
  elementIds.forEach((id) => {
    const camelCaseKey = id.replace(/-([a-z0-9])/g, (_, letter) =>
      letter.toUpperCase(),
    );
    elements[camelCaseKey] = document.getElementById(id);
  });
  let originalValues = {};
  let claimIdInt = null;
  let currentRowData = null;
  let currentClaimDetails = null;

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

  function formatDate(dateString) {
    // to be used in displaying intimation_date, date_of_loss, date_fully_documented
    if (!dateString) return "";
    const date = new Date(dateString);
    if (isNaN(date)) return "";
    return new Intl.DateTimeFormat("en-GB").format(date); // en-GB locale outputs DD/MM/YYYY
  }

  function formatDateTime(dateString) {
    // to be used in displaying last_upadeted_at
    if (!dateString) return "";
    const date = new Date(dateString);
    if (isNaN(date)) return "";

    const day = String(date.getDate()).padStart(2, "0");
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const year = date.getFullYear();

    const time = date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });

    return `${day}/${month}/${year}, ${time}`;
  }

function changeBooleanToYesOrNo(bool) {
  // Accept real booleans, the strings "true"/"false", 1/0, etc, converting 'Documented?' column to "Yes"/"No" for display in the table.
  if (bool === true || bool === "true" || bool === 1 || bool === "1") {
    return "Yes";
  }
  return "No";
}

  function initTable() {
    if ($.fn.DataTable.isDataTable("#major-table")) {
      $("#major-table").DataTable().clear().destroy();
    }

    const table = $("#major-table").DataTable({
      serverSide: true,
      processing: true,
      ajax: {
        url: "/Home/api/pending-non-motor-claims/",
        type: "POST",
        data: function (d) {
          // `d` already contains draw, start, length, search.value, order[], columns[]
          d.handler = $("#handler-filter").val();
          d.sub_status = $("#sub-status-filter").val();
          d.branch = $("#branch-filter").val();

          return d;
        },

        dataSrc: function (json) {
          // json here is your full response: { draw, recordsTotal, recordsFiltered, data }
          $("#total-pending-non-motor-claims").text(json.recordsTotal);
          return json.data; // must still return the array DataTables actually renders
        },

        beforeSend: function (xhr) {
          xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
          $("#major-table tbody").addClass("is-loading");
        },

        complete: function () {
          $("#major-table tbody").removeClass("is-loading");
          if ($.fn.DataTable.isDataTable("#major-table")) {
            $("#major-table").DataTable().columns.adjust();
          }
        },

        error: function (xhr) {
          console.error("Claim fetch failed:", xhr.responseText);
          showSwal({
            title: 'Oops...!',
            icon: 'error',
            text: "Could not load claims. Please Try Again"
          });
         // alert("Could not load claims. Please Try Again");
        },
      }, //end of ajax

      columns: [
        { data: "id", title: "claim_id", visible: false },
        { data: "name_of_insured", title: "Client" },
        { data: "cover_type", title: "Cover Type" },
        { data: "circumstance", title: "Circumstance" },
        {data: "intimation_date", title: "Intimation Date", render: (data) => formatDate(data) },
        {data: "date_of_loss", title: "Date of Loss", render: (data) => formatDate(data) },
        { data: "handler", title: "Handler" },
        { data: "days_pending", title: "Days Pending" },
        { data: "underwriter", title: "Underwriter" },
        { data: "documented", title: "Documented?", render: (data) => changeBooleanToYesOrNo(data) },
        { data: "date_fully_documented", title: "Date Documented", render: (data) => formatDate(data) },
        { data: "sub_status", title: "Sub-status" },
        { data: "branch", title: "Branch" },
        { data: "sum_insured", title: "Sum Insured", render: (data) => formatNumberWithCommas(data) },
      ],
      // Fixed percentage widths so header/body tables never drift apart on zoom.
      // Column indices map 1:1 to the `columns` array above (0 = Client ... 11 = Details).
      autoWidth: false,
      columnDefs: [
        { targets: 1, width: "15%" }, // Client
        { targets: 2, width: "5%" },  // Cover Type
        { targets: 3, width: "8%" },  // Circumstance
        { targets: 4, width: "9%" },  // Intimation Date
        { targets: 5, width: "9%" },  // Date of Loss
        { targets: 6, width: "7%" },  // Handler
        { targets: 7, width: "5%" },  // Days Pending
        { targets: 8, width: "6%" },  // Underwriter
        { targets: 9, width: "7%" },  // Documented?
        { targets: 10, width: "6%" }, // Date Documented
        { targets: 11, width: "9%" }, // Sub-status
        { targets: 12, width: "7%" }, // Branch
        { targets: 13, width: "7%" }, // sum_insured
      ],


      searchDelay: 200,
      pageLength: 100,
      lengthMenu: [100, 120, 140],
      order: [[7, "desc"]],
      scrollCollapse: true,
      scrollX: true,
      //autoWidth: true,
      paging: true,
      layout: {
        topStart: "pageLength",
        topEnd: null,
        bottomStart: "info",
        bottomEnd: "paging",
      },

      createdRow(row, data) {
        const days = Number(data.days_pending); // guards against string values
        if (!isNaN(days) && days > 10) {
          // match your actual "old" threshold
          $(row).addClass("old-claim");
        }
        if (!isNaN(days) && days > 15) {
          $(row).addClass("older-claim");
        }
      },

      initComplete: function () {
        $("#major-table tbody").removeClass("is-skeleton");
        this.api().columns.adjust();
      },
    });

    $("#searching").on("input keydown keyup change", function () {
      table.search(this.value).draw();
    });

    $("#handler-filter, #sub-status-filter, #branch-filter").on(
      "change",
      function () {
        table.draw();
      },
    );

    return table;
  }
  
  $(document).ready(function () {
    // Show 6-8 skeleton placeholder rows before the very first AJAX response arrives
    $("#major-table tbody").addClass("is-skeleton");
    initTable();
  });

  // Helper: Formats a raw number string with commas (e.g., "1000000" -> "1,000,000")
  function formatNumberWithCommas(value) {
    if (value === null || value === undefined || value === "") return "";

    // Strip out any non-digit characters except decimals
    const rawValue = value.toString().replace(/[^0-9.]/g, "");
    if (!rawValue) return "";

    // Split integer and decimal parts
    const parts = rawValue.split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");

    // Allow typing one decimal point
    return parts.length > 1 ? `${parts[0]}.${parts[1].slice(0, 2)}` : parts[0];
  }

  //For formating numbers as the user types
  const currencyInputs = document.querySelectorAll("#sum-insured, #dv-amount, #amount-paid, #add-new-claim-sum-insured, #add-new-claim-dv-amount, #add-new-claim-amount-paid");

  currencyInputs.forEach((input) => {
    input.addEventListener("input", (e) => {
      // Preserve cursor position for smooth typing
      const cursorPosition = e.target.selectionStart;
      const originalLength = e.target.value.length;

      // Apply formatting
      e.target.value = formatNumberWithCommas(e.target.value);

      // Adjust cursor position after commas are inserted
      const newLength = e.target.value.length;
      const adjustedPosition = cursorPosition + (newLength - originalLength);
      e.target.setSelectionRange(adjustedPosition, adjustedPosition);
    });
  });

  // Helper: Strips commas to get raw number for Django backend (e.g., "1,000,000" -> 1000000)
  function getRawNumericValue(formattedValue) {
    if (!formattedValue) return "";
    return formattedValue.toString().replace(/,/g, "");
  }

  // One handler for all category boxes that have data-url
  $(".left [data-url]").on("click", function () {
    if ($(this).hasClass("active-category")) {
      return; // already here, do nothing
    }
    window.location.href = $(this).data("url");
  });

  let resizeTimer;
  $(window).on("resize", function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      if ($.fn.DataTable.isDataTable("#major-table")) {
        $("#major-table").DataTable().columns.adjust();
      }
    }, 0); // debounce so it's not firing on every pixel of a drag-resize
  });

  $("#major-table tbody").on("dblclick", "tr", async function () {
    const table = $("#major-table").DataTable();
    const rowData = table.row(this).data();
    // Guard clause
    if (!rowData) return;
    const claim_id = rowData.id;

    try {
      const response = await fetch(
        `/Home/api/non-motor-claim-details-one/${encodeURIComponent(claim_id)}`,
      );

      if (!response.ok) {
        throw new Error(
          `Failed to fetch data for claim ${claim_id} : ${response.status}`,
        );
      }

      const data = await response.json();
      currentRowData = rowData;
      currentClaimDetails = data;

      // ----- Populate header -----
      elements.claimId.textContent = `Claim ${currentRowData.id}`;
      claimIdInt = currentRowData.id; //I'm making it global, since we shall use this id a lot
      elements.coverTypeHeader.textContent =
        currentRowData.cover_type || "";
      // ----- Populate form fields -----
      elements.nameOfInsured.value = currentRowData.name_of_insured || "";
      elements.claimNumber.value = currentRowData.id || "";
      elements.daysPending.value = currentRowData.days_pending ?? "";
      elements.category.value = "Non-Motor";
      elements.coverType.value = currentRowData.cover_type || "";
      elements.circumstance.value = currentRowData.circumstance || "";
      elements.intimationDate.value = currentRowData.intimation_date || "";
      elements.dateOfLoss.value = currentRowData.date_of_loss || "";
      const isDocumented = currentRowData.documented === true ||
                     currentRowData.documented === "true" ||
                     currentRowData.documented === 1 ||
                     currentRowData.documented === "1";

      elements.documented.value = isDocumented ? "true" : "false";
      elements.dateFullyDocumented.value = currentRowData.date_fully_documented || "";
      // Links (they are <a> tags)
      // elements.docLink1.href = currentClaimDetails.supporting_documents || "#";
      // elements.docLink1.textContent = currentClaimDetails.supporting_documents
      //   ? "Click to view"
      //   : "No document(s)";
      // elements.docLink1.classList.toggle(
      //   "is-disabled",
      //   !currentClaimDetails.supporting_documents,
      // );
      // elements.docLink2.href = currentClaimDetails.supporting_images || "#";
      // elements.docLink2.textContent = currentClaimDetails.supporting_images
      //   ? "Click to view"
      //   : "No image(s)";
      // elements.docLink2.classList.toggle(
      //   "is-disabled",
      //   !currentClaimDetails.supporting_images,
      // );
      elements.underwriter.value = currentRowData.underwriter || "";
      elements.branch.value = currentRowData.branch || "";
      elements.handler.value = currentRowData.handler || "";
      elements.status.value = "Pending";
      elements.subStatus.value = currentRowData.sub_status || "";
      elements.notes.value = currentClaimDetails.notes || "";
      elements.sumInsured.value =
        formatNumberWithCommas(currentRowData.sum_insured) || "0.00";
      elements.dvAmount.value =
        formatNumberWithCommas(currentRowData.dv_amount) || "0.00";
      elements.dateDvIssued.value = currentRowData.date_dv_issued || "";
      elements.dateDvReturned.value =
        currentRowData.date_dv_returned || "";
      elements.closureDate.value = currentClaimDetails.closure_date || "";
      elements.amountPaid.value = formatNumberWithCommas(currentClaimDetails.amount_paid) || "0.00";
      elements.lastUpdated.textContent = `🛈 Last updated at ${formatDateTime(currentClaimDetails.last_updated_at)}`;

      originalValuesSnapshot();

      clearChangeIndicators();

      dialog.showModal();

      originalValuesSnapshot();
      // Lock form again when opening
      inputs.forEach((input) => (input.disabled = true));
      saveBtn.disabled = true;
    } catch (error) {
      console.log(error.message);
      showSwal({
            title: 'Oops...!',
            icon: 'error',
            text: `Failed to process claim details for claim ${claim_id}`
          });
     // alert(`Failed to process claim details for claim ${claim_id}`);
    }
  });

  // Helper: converts 'subStatus' -> 'sub_status', 'dateFullyDocumented' -> 'date_fully_documented'
  function camelToSnake(str) {
    return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
  }

  function changeStringBooleansToRealBooleans(Bool) {
    const value = Bool.trim();
    if (!value || value === "") {
      return;
    } else {
      if (value.toLowerCase() === "true") {
        return true;
      }
      if (value.toLowerCase() === "false") {
        return false;
      }
    }
  }

  function createPatchPayload() {
    const payload = {};
    const allChanges = collectChanges();
    const amounts = new Set(["sumInsured", "dvAmount", "amountPaid"]);

    allChanges.forEach((change) => {
      const inputName = camelToSnake(change.field);
      const element = form.querySelector(`[name="${inputName}"]`);
      if (!element) {
        return;
      }

      if (!element.name || element.name === "") {
        return;
      }
      const parentKey = element.dataset ? element.dataset.parent : null;

      if (parentKey) {
        if (!payload[parentKey]) {
          payload[parentKey] = {};
        }
        payload[parentKey][element.name] = element.value;
        
      } else {
        if (change.field === "documented") {
          payload[element.name] = changeStringBooleansToRealBooleans(
            element.value,
          );
        } else if (amounts.has(change.field)) {
          payload[element.name] = getRawNumericValue(element.value);
        } else {
          payload[element.name] = element.value;
        }
      }
    });
    payload["category"] = "Non_Motor"; // Ensure category is always included in the payload

    return payload;
  }

  confirmChangesBtn.addEventListener("click", async () => {
    const payload_final = createPatchPayload();
    const claimId = encodeURIComponent(claimIdInt);
    const url = `/Home/api/update-claim/${claimId}/`;

    try {
      const response = await fetch(url, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify(payload_final),
      });

      if (response.ok) {
        // 1. Close the dialogs FIRST so the DOM elements remain stable
        confirmDialog.close();
        dialog.close();

        // 2. Clear state and reload table
        clearChangeIndicators();
        form.reset();
        form.scrollTop = 0;
        ancForm.reset();
        ancForm.scrollTop = 0;
        if ($.fn.DataTable.isDataTable("#major-table")) {
          $("#major-table").DataTable().ajax.reload(null, false);
        }

        // 3. Fire Swal targeting 'body' (or let showSwal run after dialogs are closed)
        await Swal.fire({
          title: "Success!",
          icon: 'success',
          text: "Claim updated Successfully🎉",
          target: "body",
          scrollbarPadding: false,
          heightAuto: false,
        });

        const data = await response.json();
        console.log("Payload sent:", payload_final);
        console.log("Claim updated successfully:", data);
        
      } else {
        confirmDialog.close(); // Close confirm dialog on error too
        const data = await response.json();
        const errors = [];
        for(const key of Object.keys(data)){
          errors.push(`[${key}] : [${data[key]}]`);
        }
        await Swal.fire({
          title: 'Oops...!',
          icon: 'error',
          text: `Failed to update Claim ${claimIdInt}. ${errors}`,
          target: "body"
        });
      }
    } catch (error) {
      confirmDialog.close();
      await Swal.fire({
        title: 'Oops...!',
        icon: 'error',
        text: `Network or Server Error ${error}`,
        target: "body"
      });
    }
  });

  // confirmChangesBtn.addEventListener("click", async () => {
  //   const payload_final = createPatchPayload();
  //   const claimId = encodeURIComponent(claimIdInt);
  //   const url = `/Home/api/update-claim/${claimId}/`;

  //   try {
  //     const response = await fetch(url, {
  //       method: "PATCH",
  //       headers: {
  //         "Content-Type": "application/json",
  //         "X-CSRFToken": getCookie("csrftoken"),
  //       },
  //       body: JSON.stringify(payload_final),
  //     });

  //     if (response.ok) {
  //       showSwal({
  //           title: 'Success🎉',
  //           icon: 'success',
  //           text: "Claim updated Successfully🎉"
  //         });
  //       //alert("Claim updated Successfully🎉");
  //       clearChangeIndicators();
  //       form.reset();
  //       form.scrollTop = 0;
  //       ancForm.reset();
  //       ancForm.scrollTop = 0;
  //       if ($.fn.DataTable.isDataTable("#major-table")) {
  //         $("#major-table").DataTable().ajax.reload(null, false);
  //       }
  //       confirmDialog.close();
  //       dialog.close();
  //       const data = await response.json();
  //       console.log("Payload sent:", payload_final);
  //       console.log("Claim updated successfully:", data);
        
  //     } else {
  //       const data = await response.json();
  //       const errors = [];
  //       for(const key of Object.keys(data)){
  //         errors.push(`[${key}] : [${data[key]}]`);
  //       }
  //       showSwal({
  //           title: 'Oops...!',
  //           icon: 'error',
  //           text: `Failed to update Claim ${claimIdInt}. ${errors}`
  //         });
  //       //alert(`Failed to update Claim ${claimIdInt}. ${errors}`));
  //       console.log(errors);
  //     }
  //   } catch (error) {
  //     showSwal({
  //           title: 'Oops...!',
  //           icon: 'error',
  //           text: `Network or Server Error: ${error}`
  //         });
  //     //alert(`Network or Server Error: ${error}`);
  //   }
  // });

  cancelConfirmBtn.addEventListener("click", function () {
    confirmDialog.close();
  });

  saveBtn.addEventListener("click", async () => {
    if(elements.status.value === 'Closed' && !elements.closureDate.value.trim()){
      showSwal({
            title: 'Warning...!',
            icon: 'warning',
            text: 'Status cannot be "Closed" while there is no Closure Date! Kindly enter the Closure Date!'
          });
    //alert('Status cannot be "Closed" while there is no Closure Date! Kindly enter the Closure Date!');
    return;
    }
    if (elements.closureDate.value && elements.status.value.trim() !== 'Closed') {
      showSwal({
            title: 'Warning...!',
            icon: 'warning',
            text: 'You cannot have a Closure Date and the status is still pending! Kindly change status to "Closed"'
          });
      //alert('You cannot have a Closure Date and the status is still pending! Kindly change status to "Closed"');
      return;
    }
    if (elements.documented.value === 'true' && !elements.dateFullyDocumented.value.trim()) {
      alert('Kindly enter the date the claim was fully documented!');
      return;
    }

    if (elements.documented.value === 'false' && elements.dateFullyDocumented.value.trim() !== '') {
      showSwal({
            title: 'Warning...!',
            icon: 'warning',
            text: "You cannot provide a 'Date Fully Documented' while 'Documented?' is set to No. Change it to Yes."
          });
      //alert("You cannot provide a 'Date Fully Documented' while 'Documented?' is set to No. Change it to Yes.");
      return;
    }
    // if(elements.status.value.trim() === 'Closed' && elements.closureDate.value.trim() !== ''){
    //   elements.subStatus.value === ''; // Clear sub-status if claim is closed
    //   elements.subStatus.disabled = true;
    // }
    const targetDates = new Set([
      "dateFullyDocumented",
      "dateDvIssued",
      "dateDvReturned",
      "closureDate",
    ]);
    const targetAmounts = new Set(["sumInsured", "dvAmount", "amountPaid"]);
    const targetBooleans = new Set(["documented"]);
    const changes_variable = await collectChanges();
    if (!changes_variable || changes_variable.length === 0) {
      showSwal({
            title: 'Oops...!',
            icon: 'info',
            text: "No Changes Made!"
          });
     // alert("No Changes Made!");
      return;
    } else {
      confirmDialog.showModal();
      container.innerHTML = "";

      changes_variable.forEach((change) => {
        const item = document.createElement("div");
        let displayFrom = change.from;
        let displayTo = change.to;

        if (targetDates.has(change.field)) {
          displayFrom = formatDate(displayFrom);
          displayTo = formatDate(displayTo);
        } else if (targetAmounts.has(change.field)) {
          displayFrom = formatNumberWithCommas(displayFrom);
          displayTo = formatNumberWithCommas(displayTo);
        } else if (targetBooleans.has(change.field)) {
          displayFrom = changeBooleanToYesOrNo(displayFrom);
          displayTo = changeBooleanToYesOrNo(displayTo);
        }

        item.className = "item";
        item.innerHTML = `
            <div class='item-header'>${change.label}</div>
            <div class='item-changes'>
              <span class='value from'>${displayFrom || "Was Empty"}</span> 
              <span class='arrow'>&rarr;</span>
              <span class='value to'>${displayTo || "To Empty"}</span>   
            </div>
          `;

        container.appendChild(item);
      });
    }
  });

  cancelEditing.addEventListener("click", function () {
    inputs.forEach((input) => {
      input.disabled = true;
    });
    clearChangeIndicators();
    saveBtn.disabled = true;

    elements.claimId.textContent = `Claim ${currentRowData.id}`;
    elements.coverTypeHeader.textContent =
        currentRowData.cover_type || "";
    elements.nameOfInsured.value = currentRowData.name_of_insured || "";
    elements.claimNumber.value = currentRowData.id || "";
    elements.daysPending.value = currentRowData.days_pending ?? "";
    elements.category.value = "Non-Motor";
    elements.coverType.value = currentRowData.cover_type || "";
    elements.circumstance.value = currentRowData.circumstance || "";
    elements.intimationDate.value = currentRowData.intimation_date || "";
    elements.dateOfLoss.value = currentRowData.date_of_loss || "";
    const isDocumented = currentRowData.documented === true ||
                     currentRowData.documented === "true" ||
                     currentRowData.documented === 1 ||
                     currentRowData.documented === "1";

    elements.documented.value = isDocumented ? "true" : "false";
    elements.dateFullyDocumented.value = currentRowData.date_fully_documented || "";

    // elements.docLink1.href = currentClaimDetails.supporting_documents || "#";
    // elements.docLink1.textContent = currentClaimDetails.supporting_documents
    //   ? "Click to view"
    //   : "No document(s)";
    // elements.docLink1.classList.toggle(
    //   "is-disabled",
    //   !currentClaimDetails.supporting_documents,
    // );
    // elements.docLink2.href = currentClaimDetails.supporting_images || "#";
    // elements.docLink2.textContent = currentClaimDetails.supporting_images
    //   ? "Click to view"
    //   : "No image(s)";
    // elements.docLink2.classList.toggle(
    //   "is-disabled",
    //   !currentClaimDetails.supporting_images,
    // );

    elements.underwriter.value = currentRowData.underwriter || "";
    elements.branch.value = currentRowData.branch || "";
    elements.handler.value = currentRowData.handler || "";
    elements.status.value = "Pending"; // or whatever your status field is
    elements.subStatus.value = currentRowData.sub_status || "";
    elements.notes.value = currentClaimDetails.notes || "";
    elements.sumInsured.value =
      formatNumberWithCommas(currentRowData.sum_insured) || "0.00";
    elements.dvAmount.value =
      formatNumberWithCommas(currentClaimDetails.dv_amount) || "0.00";
    elements.dateDvIssued.value = currentClaimDetails.date_dv_issued || "";
    elements.dateDvReturned.value = currentClaimDetails.date_dv_returned || "";
    elements.amountPaid.value = formatNumberWithCommas(currentClaimDetails.amount_paid) || "0.00";
    elements.lastUpdated.textContent = `🛈 Last updated at ${formatDateTime(currentClaimDetails.last_updated_at)}`;
    
    clearChangeIndicators();
  });

  // if(dialog.open){
  //   const listeners = [
  //     elements.motorClass,
  //     elements.circumstance,
  //     elements.documented,
  //     elements.dateFullyDocumented,
  //     elements.status,
  //     elements.subStatus,
  //     elements.assessor,
  //     elements.notes,
  //     elements.sumInsured,
  //     elements.dvAmount,
  //     elements.dateDvIssued,
  //     elements.dateDvReturned,
  //     elements.closureDate,
  //   ];

  //   listeners.forEach((element) => {
  //     // Guard clause: skip if element doesn't exist on page
  //     if (!element) return;

  //     // Track the initial value loaded from DB
  //     const initialValue = element.value;

  //     // Use 'input' for text fields and 'change' for selects/dates
  //     ["input", "change"].forEach((eventType) => {
  //       element.addEventListener(eventType, function () {
  //         // Look for an existing indicator right after this field
  //         let indicator = this.nextElementSibling;
  //         const isModified = this.value !== initialValue;

  //         // Check if indicator already exists
  //         const hasIndicator =
  //           indicator && indicator.classList.contains("change-indicator");

  //         if (isModified) {
  //           // If not created yet, build and insert it
  //           if (!hasIndicator) {
  //             indicator = document.createElement("p");
  //             indicator.className = "change-indicator";
  //             indicator.style.color = "#dc2626"; /* Clean red shade */
  //             indicator.style.fontSize =
  //               "0.55rem"; /* 0.5rem is extremely tiny/unreadable */
  //             indicator.style.marginTop = "0.1rem";

  //             // Insert right after the input/select element
  //             this.after(indicator);
  //           }
  //           indicator.textContent = "ⓘ NB: You have changed this one";
  //         } else {
  //           // If user changed value back to original, remove the indicator
  //           if (hasIndicator) {
  //             indicator.remove();
  //           }
  //         }
  //       });
  //     });
  //   });
  //   }

  //Helper to read, normalize, and sanitize input values

  // After the `elements` object is created

  const editableFields = [
    elements.circumstance,
    elements.documented,
    elements.dateFullyDocumented,
    elements.status,
    elements.subStatus,
    elements.notes,
    elements.dvAmount,
    elements.dateDvIssued,
    elements.dateDvReturned,
    elements.closureDate,
    elements.amountPaid,
  ];

  function clearChangeIndicators() {
    form.querySelectorAll(".change-indicator").forEach((el) => el.remove());
  }

  function updateChangeIndicator(el) {
    // Remove existing indicator (if any)
    let indicator = el.nextElementSibling;
    if (indicator?.classList.contains("change-indicator")) {
      indicator.remove();
    }

    // Map the DOM element back to the key used in originalValues
    const idToKey = {
      "cover-type": "coverType",
      "circumstance": "circumstance",
      "documented": "documented",
      "date-fully-documented": "dateFullyDocumented",
      "status": "status",
      "sub-status": "subStatus",
      "notes": "notes",
      "dv-amount": "dvAmount",
      "date-dv-issued": "dateDvIssued",
      "date-dv-returned": "dateDvReturned",
      "closure-date": "closureDate",
      "amount-paid": "amountPaid",
    };

    const key = idToKey[el.id];
    if (!key || !originalValues) return;

    let current = el.value;
    if (key === "sumInsured" || key === "dvAmount") {
      current = getRawNumericValue(current);
    }
    current = (current ?? "").toString().trim();

    const original = originalValues[key] ?? "";

    if (current !== original) {
      indicator = document.createElement("p");
      indicator.className = "change-indicator";
      indicator.style.cssText =
        "color:#dc2626;font-size:0.55rem;margin-top:0.1rem;";
      indicator.textContent = "ⓘ NB: You have changed this value";
      el.after(indicator);
    }
  }

  // Attach ONCE
  editableFields.forEach((el) => {
    if (!el) return;
    ["input", "change"].forEach((evt) => {
      el.addEventListener(evt, () => updateChangeIndicator(el));
    });
  });

  function getFormValues() {
    const normalize = (val) => (val ?? "").toString().trim();

    return {
      circumstance: normalize(elements.circumstance.value),
      documented: normalize(elements.documented.value),
      dateFullyDocumented: normalize(elements.dateFullyDocumented.value),
      status: normalize(elements.status.value),
      subStatus: normalize(elements.subStatus.value),
      notes: normalize(elements.notes.value),
      sumInsured: normalize(getRawNumericValue(elements.sumInsured.value)),
      dvAmount: normalize(getRawNumericValue(elements.dvAmount.value)),
      dateDvIssued: normalize(elements.dateDvIssued.value),
      dateDvReturned: normalize(elements.dateDvReturned.value),
      closureDate: normalize(elements.closureDate.value),
      amountPaid: normalize(getRawNumericValue(elements.amountPaid.value)),
    };
  }

  // Human-readable labels
const fieldLabels = {
  trigger: "Trigger",
  coverType: "Cover Type",
  circumstance: "Circumstance",
  documented: "Documented?",
  dateFullyDocumented: "Date Fully Documented",
  status: "Status",
  subStatus: "Sub-status",
  notes: "Notes",
  sumInsured: "Sum Insured",
  dvAmount: "DV Amount",
  dateDvIssued: "Date DV Issued",
  dateDvReturned: "Date DV Returned",
  closureDate: "Closure Date",
  amountPaid: "Amount Paid",
};

  function originalValuesSnapshot() {
    //NB: Only for the editable parts in the claims-details-dialog
    originalValues = getFormValues();
  }

  function collectChanges() {
    let changes = [];
    const currentValues = getFormValues();

    for (const key of Object.keys(originalValues)) {
      const from = originalValues[key];
      const to = currentValues[key];
      const label = fieldLabels[key] ?? key; // or const name = fieldLabels[key]? fieldLabels[key] : key; /const name = fieldLabels[key] || key;

      if (from !== to) {
        changes.push({
          field: key,
          label: label,
          from: from,
          to: to,
        });
      }
    }
    return changes;
  }

  //=======CLAIM DETAILS DIALOG========

  form.addEventListener("submit", (e) => {
    e.preventDefault();
  });

  editBtn.addEventListener("click", function () {
    inputs.forEach((input) => {
      input.disabled = false;
    });
    if(elements.documented.value.trim() === 'false'){
    elements.dateFullyDocumented.disabled = true;
    elements.dateFullyDocumented.classList.add('add-new-claim-date-fully-documented-disabled');
    elements.dateFullyDocumented.value = "";
    } else{
      elements.dateFullyDocumented.disabled = false;
      elements.dateFullyDocumented.classList.remove('add-new-claim-date-fully-documented-disabled');
    }

    const uneditableParts = [
      elements.coverType,
      elements.nameOfInsured,
      elements.claimNumber,
      elements.daysPending,
      elements.category,
      elements.intimationDate,
      elements.dateOfLoss,
      elements.handler,
      elements.branch,
      elements.underwriter,
      elements.sumInsured,
    ];

    uneditableParts.forEach((uneditable) => {
      uneditable.disabled = true;
    });

    saveBtn.disabled = false;
  });

  closeDialogBtn.addEventListener("click", function () {
    if(confirmDialog.open){
      confirmDialog.close();
    }
    clearChangeIndicators();
    originalValues = {};
    form.reset();
    form.scrollTop = 0;
    dialog.close();
    

    // Optional but nice: put the form back into locked state
    inputs.forEach((input) => (input.disabled = true));
    saveBtn.disabled = true;
  });


  


// const addNewClaimSumInsured = document.getElementById('add-new-claim-sum-insured');
// const addNewClaimDvAmount = document.getElementById('add-new-claim-dv-amount');

// const addNewClaimCurrencyInputs = [addNewClaimSumInsured, addNewClaimDvAmount];

// addNewClaimCurrencyInputs.forEach((input) => {
//   input.addEventListener("input", (e) => {
//     const cursorPosition = e.target.selectionStart;
//     const originalLength = e.target.value.length;

//     e.target.value = formatNumberWithCommas(e.target.value);

//     const newLength = e.target.value.length;
//     const adjustedPosition = cursorPosition + (newLength - originalLength);
//     e.target.setSelectionRange(adjustedPosition, adjustedPosition);
//   });
// });


function resetAncDisabledFields() {
  // Sub-status
  // addNewClaimSubStatus.disabled = true;
  // addNewClaimSubStatus.classList.add('add-new-claim-sub-status-disabled');
  // addNewClaimSubStatus.value = "";

  // Date Fully Documented
  addNewClaimDateFullyDocumented.disabled = true;
  addNewClaimDateFullyDocumented.classList.add('add-new-claim-date-fully-documented-disabled');
  addNewClaimDateFullyDocumented.value = "";
}

// Call it once on load
resetAncDisabledFields();

// When opening the dialog
addNewClaimBtn.addEventListener('click', function () {
  ancDialog.showModal();
  ancForm.scrollTop = 0;
  resetAncDisabledFields();   // safety
});


addNewClaimClosureDate.disabled = true;
addNewClaimClosureDate.classList.add('add-new-claim-closure-date-disabled');
// Status → Sub-status
addNewClaimStatus.addEventListener('change', function () {
  if (addNewClaimStatus.value.trim() === 'Pending') {
    // addNewClaimSubStatus.disabled = false;
    // addNewClaimSubStatus.classList.remove('add-new-claim-sub-status-disabled');
    addNewClaimClosureDate.disabled = true;
    addNewClaimClosureDate.classList.add('add-new-claim-closure-date-disabled');
    addNewClaimClosureDate.value = "";
  } else {
    // addNewClaimSubStatus.disabled = true;
    // addNewClaimSubStatus.classList.add('add-new-claim-sub-status-disabled');
    // addNewClaimSubStatus.value = "";
    addNewClaimClosureDate.disabled = false;
    addNewClaimClosureDate.classList.remove('add-new-claim-closure-date-disabled');
  }
});

// Documented? → Date Fully Documented
addNewClaimDocumented.addEventListener('change', function () {
  if (addNewClaimDocumented.value.trim() === 'true') {
    addNewClaimDateFullyDocumented.disabled = false;
    addNewClaimDateFullyDocumented.classList.remove('add-new-claim-date-fully-documented-disabled');
  } else {
    addNewClaimDateFullyDocumented.disabled = true;
    addNewClaimDateFullyDocumented.classList.add('add-new-claim-date-fully-documented-disabled');
    addNewClaimDateFullyDocumented.value = "";
  }
});


// Documented? → Date Fully Documented (claim-details-dialog)
elements.documented.addEventListener('change', function () {
  if (elements.documented.value.trim() === 'true') {
    elements.dateFullyDocumented.disabled = false;
    elements.dateFullyDocumented.classList.remove('add-new-claim-date-fully-documented-disabled');
  } else {
    elements.dateFullyDocumented.disabled = true;
    elements.dateFullyDocumented.classList.add('add-new-claim-date-fully-documented-disabled');
    elements.dateFullyDocumented.value = "";
  }
});


// elements.subStatus.classList.add('add-new-claim-sub-status-disabled');
// elements.status.addEventListener('change', function(){
//   if(elements.status.value.trim() === 'Closed'){
//     elements.subStatus.disabled = true;
//     elements.subStatus.value = '';
//     elements.subStatus.classList.add('add-new-claim-sub-status-disabled');
//   } else{
//     elements.subStatus.disabled = false;
//     elements.subStatus.classList.remove('add-new-claim-sub-status-disabled');
//     elements.subStatus.value = currentRowData.sub_status || '';
//   }
// });

addNewClaimDateDvIssued.disabled = true;
addNewClaimDateDvIssued.classList.add('disabled-field');
addNewClaimDateDvReturned.disabled = true;
addNewClaimDateDvReturned.classList.add('disabled-field');
addNewClaimAmountPaid.disabled = true;
addNewClaimAmountPaid.classList.add('disabled-field');

addNewClaimDvAmount.addEventListener('input', function(){
  if(getRawNumericValue(addNewClaimDvAmount.value.trim()) !== '' && Number(getRawNumericValue(addNewClaimDvAmount.value.trim())) > 0){
    addNewClaimDateDvIssued.disabled = false;
    addNewClaimDateDvIssued.classList.remove('disabled-field');
    addNewClaimDateDvReturned.disabled = false;
    addNewClaimDateDvReturned.classList.remove('disabled-field');
    addNewClaimAmountPaid.disabled = false;
    addNewClaimAmountPaid.classList.remove('disabled-field');
  } else {
    addNewClaimDateDvIssued.disabled = true;
    addNewClaimDateDvIssued.classList.add('disabled-field');
    addNewClaimDateDvReturned.disabled = true;
    addNewClaimDateDvReturned.classList.add('disabled-field');
    addNewClaimAmountPaid.disabled = true;
    addNewClaimAmountPaid.classList.add('disabled-field');
  }
})


// if(elements.documented.value === 'false'){
//   elements.dateFullyDocumented.disabled = true;
//   elements.dateFullyDocumented.classList.add('add-new-claim-date-fully-documented-disabled');
//   elements.dateFullyDocumented.value = "";
// }
// // Documented? → Date Fully Documented
// elements.documented.addEventListener('change', function () {
//   if (elements.documented.value.trim() === 'true') {
//     elements.dateFullyDocumented.disabled = false;
//     elements.dateFullyDocumented.classList.remove('add-new-claim-date-fully-documented-disabled');
//   } else {
//     elements.dateFullyDocumented.disabled = true;
//     elements.dateFullyDocumented.classList.add('add-new-claim-date-fully-documented-disabled');
//     elements.dateFullyDocumented.value = "";
//   }
// });

const ancNames =['name_of_insured','category','circumstance','cover_type','intimation_date','date_of_loss',
                  'documented','date_fully_documented','underwriter','branch',
                  'handler','status','sub_status','notes','sum_insured','dv_amount','date_dv_issued','date_dv_returned',
                  'closure_date', 'amount_paid'
]


function createPostPayload(){

  postPayload = {};

  ancNames.forEach(name =>{
    const element = ancForm.querySelector(`[name=${name}]`);
    if(!element) return;  
    if(!element.value || element.value === '' ){return;}
    if(!name || name === ''){return;}
     const parentKey = element.dataset ? element.dataset.parent : null;

     if(parentKey){
      if(!postPayload[parentKey]){
        postPayload[parentKey] = {};
      }
      postPayload[parentKey][name] = element.value;

     } else{
       if(name === 'documented'){
        postPayload[name] = changeStringBooleansToRealBooleans(element.value);
      } else if(name === 'sum_insured' || name === 'dv_amount' || name === 'amount_paid'){
        postPayload[name] = getRawNumericValue(element.value);
      } else{
        postPayload[name] = element.value
        }
     }

});
  return postPayload;
}


ancForm.addEventListener('submit', (e) => {
  e.preventDefault();
  e.stopPropagation();
})


submitNewClaimBtn.addEventListener('click', async() => {
  if(!ancForm.checkValidity()){
    ancForm.reportValidity();
    return;
  }
const finalPostPayload = await createPostPayload();
console.log (finalPostPayload);
console.table (finalPostPayload);

try{
const response = await fetch('/Home/api/add-new-claim/', {
  method: 'POST',
  headers: {
    "Content-Type" : "application/json",
    "X-CSRFToken" : getCookie("csrftoken")
  },
  body : JSON.stringify(finalPostPayload)
  }
);

if(response.ok){
  const data = await response.json();
  console.log(`Claim Added Successfully: ` + data);
  showSwal({
            title: 'Success🎉',
            icon: 'success',
            text: `Claim Added Successfully🎉 and asigned number "${data.id}"`
          });
  //alert(`Claim Added Successfully🎉 and asigned number "${data.id}"`);

  postPayload = null;
  ancForm.reset();
  ancForm.scrollTop = 0;

  // addNewClaimSubStatus.disabled = true;
  // addNewClaimSubStatus.classList.add('add-new-claim-sub-status-disabled');
  // document.getElementById('add-new-claim-category').value = 'Non-Motor';

  if($.fn.DataTable.isDataTable('#major-table')){
    $('#major-table').DataTable().ajax.reload(null, false);
  }
  ancDialog.close();
  
} else{
  const data = await response.json();
  console.log (response.status);
  console.log (data);
  const errors = [];
  for(const key of Object.keys(data)){
    errors.push(`[${key}] : [${data[key]}]`);
  }
  showSwal({
            title: 'Oops...!',
            icon: 'error',
            text: `${errors}`
          });
  //alert(errors);
}

} catch(err){
  showSwal({
            title: 'Oops...!',
            icon: 'error',
            text: "Failed to create the Claim. Kindly retry again"
          });
 // alert("Failed to create the Claim. Kindly retry again");
  console.log(err)
}

});

ancCancelDialogBtn.addEventListener('click', function(){
  ancDialog.close();
  postPayload = null;
  ancForm.reset();
  ancForm.scrollTop = 0;
  addNewClaimSubStatus.value = "";
});

// Define the option sets per status
const subStatusOptions = {
  default: [
    { value: '', label: 'Select sub-status…', disabled: true, selected: true },
    { value: 'Pending with underwriter', label: 'Pending with underwriter' },
    { value: 'Pending with client', label: 'Pending with client' },
  ],
  Closed: [
    { value: '', label: 'Select sub-status…', disabled: true, selected: true },
    { value: 'Paid', label: 'Paid' },
    { value: 'Rejected', label: 'Rejected' },
  ],
};

function populateAddNewClaimSubStatus(options) {
  addNewClaimSubStatus.innerHTML = ''; // clear existing options
  options.forEach(opt => {
    const el = document.createElement('option');
    el.value = opt.value;
    el.textContent = opt.label;
    if (opt.disabled) el.disabled = true;
    if (opt.selected) el.selected = true;
    addNewClaimSubStatus.appendChild(el);
  });
}

addNewClaimStatus.addEventListener('change', function(){
  const options = addNewClaimStatus.value === 'Closed'
    ? subStatusOptions.Closed
    : subStatusOptions.default;
  populateAddNewClaimSubStatus(options);
})

function populateElementsSubStatus(options) {
  elements.subStatus.innerHTML = ''; // clear existing options
  options.forEach(opt => {
    const el = document.createElement('option');
    el.value = opt.value;
    el.textContent = opt.label;
    if (opt.disabled) el.disabled = true;
    if (opt.selected) el.selected = true;
    elements.subStatus.appendChild(el);
  });
}


if(elements.status.value === 'Closed'){
  const options = subStatusOptions.Closed;
  populateElementsSubStatus(options);
} else{
  const options = subStatusOptions.default;
  populateElementsSubStatus(options);
}

elements.status.addEventListener('change', function(){
  const options = elements.status.value === 'Closed'
    ? subStatusOptions.Closed
    : subStatusOptions.default;
  populateElementsSubStatus(options);
})