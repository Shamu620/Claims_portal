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

  function changeCategoriesToUserFriendly(category){
        if (category ==="Non_Motor"){return "Non-Motor"};
        if(category ==="Motor"){return "Motor"};
        if(category ==="Credit_Life"){return "Credit Life"}

    }


function initTable() {
  if ($.fn.DataTable.isDataTable("#major-table")) {
    $("#major-table").DataTable().clear().destroy();
  }

  const table = $("#major-table").DataTable({
    serverSide: true,
    processing: true,
    ajax: {
      url: "/Home/api/all-pending-claims/",
      type: "POST",
      data: function (d) {
        // `d` already contains draw, start, length, search.value, order[], columns[]
        d.handler = $("#handler").val();
        d.sub_status=$('#sub-status').val();
        d.branch = $("#branch").val();

        return d;
      },

      dataSrc: function (json) {
         // json here is your full response: { draw, recordsTotal, recordsFiltered, data }
         $("#total-pending-claims").text(json.recordsTotal);
         return json.data; // must still return the array DataTables actually renders
        },

      beforeSend: function (xhr) {
        xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        $("#major-table tbody").addClass("is-loading");
      },

      complete: function () {
          $("#major-table tbody").removeClass("is-loading");
          if ($.fn.DataTable.isDataTable('#major-table')) {
         $('#major-table').DataTable().columns.adjust();
          }
        },

      error: function (xhr) {
        console.error("Claim fetch failed:", xhr.responseText);
        alert("Could not load claims. Please Try Again");
      },
    }, //end of ajax

    columns: [
      { data: "name_of_insured", title: "Client"},
      { data: "category", title: "Category", render:(data)=> changeCategoriesToUserFriendly(data)},
      { data: "underwriter", title: "Underwriter" },
      { data: "intimation_date", title: "Intimation Date", render: (data) => formatDate(data)},
      { data: "date_of_loss", title: "Date of Loss", render: (data) => formatDate(data) },
      { data: "days_pending", title: "Days pending" },
      { data: "documented", title: "Documented?" },
      { data: "date_fully_documented", title: "Date Documented", render: (data) => formatDate(data) },
      { data: "handler", title: "Handler" },
      { data: "sub_status", title: "Sub-status" },
      { data: "branch", title: "Branch" },
      { data: "sum_insured", title: "Sum Insured", render: (data) => formatNumberWithCommas(data) },
    ],

    // Fixed percentage widths so header/body tables never drift apart on zoom.
    // Column indices map 1:1 to the `columns` array above (0 = Client ... 11 = Details).
    autoWidth: false,
    columnDefs: [
      { targets: 0, width: "15%" }, // Client
      { targets: 1, width: "8%" }, // Category
      { targets: 2, width: "9%" }, // Underwriter
      { targets: 3, width: "9%" }, // Intimation Date
      { targets: 4, width: "9%" }, // Date of Loss
      { targets: 5, width: "7%" }, // Days pending
      { targets: 6, width: "5%" }, // Documented?
      { targets: 7, width: "9%" }, // Date Documented
      { targets: 8, width: "7%" }, // Handler
      { targets: 9, width: "8%" }, // Sub-status
      { targets: 10, width: "7%" }, // Branch
      { targets: 11, width: "7%" }, // Details
    ],

    searchDelay: 200,
    pageLength: 100,
    lengthMenu: [100, 120, 140],
    order: [[5, "desc"]],
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

 $("#searching").on("keyup search input", function () {
      table.search(this.value).draw();
    });

  $("#handler, #sub-status, #branch").on("change", function () {
    table.draw();
  });

  return table;
}

$(document).ready(function () {
  // Show 6-8 skeleton placeholder rows before the very first AJAX response arrives
  $("#major-table tbody").addClass("is-skeleton");
  initTable();
});

// One handler for all category boxes that have data-url
  $('.left [data-url]').on('click', function () {
    if($(this).hasClass('active-category')){
      return;  // already here, do nothing
    }
    window.location.href = $(this).data('url');
  });


  let resizeTimer;
$(window).on('resize', function () {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(function () {
    if ($.fn.DataTable.isDataTable('#major-table')) {
      $('#major-table').DataTable().columns.adjust();
    }
  }, 0); // debounce so it's not firing on every pixel of a drag-resize
});








