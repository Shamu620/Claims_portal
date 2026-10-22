const loadingDialog = document.getElementById('loading-dialog');
    const totalClaimsDownloadBtn = document.getElementById('total-claims-download-btn');
    const closedClaimsDownloadBtn = document.getElementById('closed-claims-download-btn');
    const pendingClaimsDownloadBtn = document.getElementById('pending-claims-download-btn');
    let searchTimeout;
    let filteringPayload = {};
    let totalClaimsRows;
    let closedClaimsRows;
    let pendingClaimsRows;
    const elementIds = [
        //MOTOR
        'motor_dialog',
        'motor-claim-id',
        'motor-dialog-close-x-btn',
        'motor-name_of_insured',
        'motor-intimation_date',
        'motor-date_of_loss',
        'motor-circumstance',
        'motor-sum_insured',
        'motor-registration_number',
        'motor-motor_class',
        'motor-assessor',
        'motor-underwriter',
        'motor-branch',
        'motor-handler',
        'motor-status',
        'motor-sub_status',
        'motor-documented',
        'motor-date_fully_documented',
        'motor-date_dv_issued',
        'motor-dv_amount',
        'motor-date_dv_returned',
        'motor-amount_paid',
        'motor-closure_date',
        'motor-tat_dv',
        'motor-tat_cl',
        'motor-days_pending',
        'motor-notes',
        'motor-created-at',
        'motor-updated-at',
        'motor-dialog-close-btn',
        'motor-status-badge',

        //NON-MOTOR
        'non_motor_dialog',
        'non_motor-claim-id',
        'non_motor-dialog-close-x-btn',
        'non_motor-name_of_insured',
        'non_motor-intimation_date',
        'non_motor-date_of_loss',
        'non_motor-circumstance',
        'non_motor-sum_insured',
        'non_motor-cover_type',
        'non_motor-underwriter',
        'non_motor-branch',
        'non_motor-handler',
        'non_motor-status',
        'non_motor-sub_status',
        'non_motor-documented',
        'non_motor-date_fully_documented',
        'non_motor-date_dv_issued',
        'non_motor-dv_amount',
        'non_motor-date_dv_returned',
        'non_motor-amount_paid',
        'non_motor-closure_date',
        'non_motor-tat_dv',
        'non_motor-tat_cl',
        'non_motor-days_pending',
        'non_motor-notes',
        'non_motor-created-at',
        'non_motor-updated-at',
        'non_motor-dialog-close-btn',
        'non_motor-status-badge',

        //CREDIT_LIFE
        'credit_life_dialog',
        'credit_life-claim-id',
        'credit_life-dialog-close-x-btn',
        'credit_life-name_of_insured',
        'credit_life-intimation_date',
        'credit_life-date_of_loss',
        'credit_life-circumstance',
        'credit_life-sum_insured',
        'credit_life-claim_trigger',
        'credit_life-underwriter',
        'credit_life-branch',
        'credit_life-handler',
        'credit_life-status',
        'credit_life-sub_status',
        'credit_life-documented',
        'credit_life-date_fully_documented',
        'credit_life-date_dv_issued',
        'credit_life-dv_amount',
        'credit_life-date_dv_returned',
        'credit_life-amount_paid',
        'credit_life-closure_date',
        'credit_life-tat_dv',
        'credit_life-tat_cl',
        'credit_life-days_pending',
        'credit_life-notes',
        'credit_life-created-at',
        'credit_life-updated-at',
        'credit_life-dialog-close-btn',
        'credit_life-status-badge'
    ];
    
    const elements ={};
    elementIds.forEach((id) => {
    const camelCaseKey = id.replace(/[-_]([a-z0-9])/g, (_, letter) =>
      letter.toUpperCase(),
    );
    elements[camelCaseKey] = document.getElementById(id);
  });

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

    function changeBooleanToYesOrNo(bool) {
  // Accept real booleans, the strings "true"/"false", 1/0, etc, converting 'Documented?' column to "Yes"/"No" for display in the table.
  if (bool === true || bool === "true" || bool === 1 || bool === "1") {
    return "Yes";
  }
  return "No";
}

    $(window).on('resize', function(){
        if($.fn.DataTable.isDataTable('#total-claims-table')){
            $('#total-claims-table').DataTable().columns.adjust();
        };

        if($.fn.DataTable.isDataTable('#closed-claims-table')){
            $('#closed-claims-table').DataTable().columns.adjust();
        };

        if($.fn.DataTable.isDataTable('#pending-claims-table')){
            $('#pending-claims-table').DataTable().columns.adjust();
        }
    });

    function changeCategoriesToUserFriendly(category){
        if (category ==="Non_Motor"){return "Non-Motor"};
        if(category ==="Motor"){return "Motor"};
        if(category ==="Credit_Life"){return "Credit Life"}

    }



    function initTotalClaimsTable(){
        if($.fn.DataTable.isDataTable("#total-claims-table")){
            $('#total-claims-table').DataTable().clear().destroy();
        }

        const table = $("#total-claims-table").DataTable({
            serverSide: true,
            processing: true,
            ajax: {
                url: "/Home/api/total-claims/",
                type: "POST",
                data: function(d){
                    d.status = $('#total-claims-status-filter').val();
                    d.branch = $('#total-claims-branch-filter').val();
                    d.handler = $('#total-claims-handler-filter').val();
                    d.underwriter = $('#total-claims-underwriter-filter').val();
                    d.category = $('#total-claims-category-filter').val();
                    return d;
                },
                beforeSend: function(xhr){
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                    $('#total-claims-table tbody').addClass('is-loading');
                },
                dataSrc: function(json){
                    //source/capture the total claims number from here
                    $('#total-claims-count').text(formatNumberWithCommas(json.recordsTotal));
                    return json.data;
                },
                complete: function(json){
                    $('#total-claims-table tbody').removeClass('is-loading');
                    if($.fn.DataTable.isDataTable('#total-claims-table')){
                        $('#total-claims-table').DataTable().columns.adjust();
                    }
                },
                error: function(xhr){
                    console.error("Claims fetch failed:", xhr.responseText);
                    alert("Could not load claims. Kindly check your network and try again");
                }

            },//end of ajax

            layout: {
                topStart: "pageLength",
                topEnd: null,
                bottomStart: "info",
                bottomEnd: "paging"
            },

            columns: [
                {data: "name_of_insured", title: "Client"},
                {data: "status", title: "Status"},
                {data: "category", title: "Category", render:(data) => changeCategoriesToUserFriendly(data)},
                {data: "underwriter", title: "Underwriter"},
                {data: "intimation_date", title: "Intimation Date", render: (data) => formatDate(data)},
                {data: "date_of_loss", title: "Date of Loss", render: (data) => formatDate(data)},
                {data: "handler", title: "Handler"},
                {data: "branch", title: "Branch"},
                {data: "sum_insured", title: "Sum Insured", render: (data) => formatNumberWithCommas(data)},
                {data: "id", title: "client_id", visible: false}
            ],

            autoWidth: false,
            columnDefs: [
                { targets: 0, width: "15%" }, //Client
                { targets: 1, width: "10%" }, //Status
                { targets: 2, width: "10%" }, //Category
                { targets: 3, width: "15%" }, //Underwriter
                { targets: 4, width: "10%" }, //Intimation Date
                { targets: 5, width: "10%" }, //Date of Loss
                { targets: 6, width: "10%" }, //Handler
                { targets: 7, width: "10%" }, //Branch
                { targets: 8, width: "10%" }, //Sum Insured
            ],

            scrollCollapse: true,
            scrollX: true,
            scrollY: "45dvh",
            searchDelay: 200,
            pageLength: 50,
            lengthMenu: [50, 70, 100],
            paging: true,
            order: [[4, "desc"]],

            initComplete: function(){
                $('#total-claims-table tbody').removeClass("is-skeleton");
                this.api().columns.adjust();
            },
        });


        $('#total-claims-search').on('keyup change', function () {
            const inputElement = this;

            // Clear the previous timeout on every keystroke
            clearTimeout(searchTimeout);

            // Wait 3 seconds after the user stops typing to execute the search
            searchTimeout = setTimeout(() => {
                table.search(inputElement.value).draw();
            }, 300);
        });

        $('#total-claims-status-filter, #total-claims-category-filter, #total-claims-underwriter-filter, #total-claims-handler-filter, #total-claims-branch-filter').on(
            'change', function(){
                table.draw();
            }
        );

        return table;

    }

    function totalClaimsRowEventListener(){
        const captureTableBody = function (){
            if($.fn.DataTable.isDataTable('#total-claims-table')){
                return $('#total-claims-table tbody');
            } else{ return; }
        }

        const tableBody = captureTableBody();

        tableBody.on('dblclick', 'tr', async function(){
        const table = $('#total-claims-table').DataTable();
        const rowData = table.row(this).data();
        if(!rowData){ return; }

        const claim_id = rowData.id;
        const claim_category = rowData.category;
        
        const url = `/Home/api/total-claims-details-one/${decodeURIComponent(claim_id)}/${decodeURIComponent(claim_category)}/`
        try{
            loadingDialog.showModal(); //Show the spinner as we wait the backed fetch (in case of delayals)

            const response = await fetch(url);
             if(!response.ok){
                throw new Error(`Failed to load data for claim ${claim_id}: ${response.status}, ${response.statusText}`);
             }

             const data = await response.json();

             loadingDialog.close(); //Remove the spinner after the data is fetched from the backend

             if(claim_category == "Motor"){
              populateMotorDetailsDialog(rowData, data);
             }
             else if(claim_category == "Non_Motor"){
              populateNonMotorDetailsDialog(rowData, data);
             }
             else if (claim_category == "Credit_Life"){
              populateCreditLifeDetailsDialog(rowData, data);
             }
             else {
              alert("Invalid category!");
              return;
             }

            //  alert(data);
             console.table(data);


        } catch(err){
            alert(`Failed to load the details for claim number ${claim_id}`);
            console.log(err)
        }

        // alert(`dblclick worked and the id is ${claim_id}, and category is ${claim_category}`);
    });
    }
    
    function initClosedClaimsTable(){
        if($.fn.DataTable.isDataTable("#closed-claims-table")){
            $('#closed-claims-table').DataTable().clear().destroy();
        }

        const table = $("#closed-claims-table").DataTable({
            serverSide: true,
            processing: true,
            ajax: {
                url: "/Home/api/closed-claims/",
                type: "POST",
                data: function(d){
                    d.subStatus = $('#closed-claims-sub-status-filter').val();
                    d.branch = $('#closed-claims-branch-filter').val();
                    d.handler = $('#closed-claims-handler-filter').val();
                    d.underwriter = $('#closed-claims-underwriter-filter').val();
                    d.category = $('#closed-claims-category-filter').val();
                    return d;
                },
                beforeSend: function(xhr){
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                    $('#closed-claims-table tbody').addClass('is-loading');
                },
                dataSrc: function(json){
                    //source/capture the total closed claims number from here
                    $('#closed-claims-count').text(formatNumberWithCommas(json.recordsTotal));
                    return json.data;
                },
                complete: function(json){
                    $('#closed-claims-table tbody').removeClass('is-loading');
                    if($.fn.DataTable.isDataTable('#closed-claims-table')){
                        $('#closed-claims-table').DataTable().columns.adjust();
                    }
                },
                error: function(xhr){
                    console.error("Claims fetch failed:", xhr.responseText);
                    alert("Could not load claims. Kindly check your network and try again");
                }

            },//end of ajax

            layout: {
                topStart: "pageLength",
                topEnd: null,
                bottomStart: "info",
                bottomEnd: "paging"
            },

            columns: [
                {data: "name_of_insured", title: "Client"},
                {data: "category", title: "Category", render:(data)=> changeCategoriesToUserFriendly(data)},
                {data: "underwriter", title: "Underwriter"},
                {data: "intimation_date", title: "Intimation Date", render: (data) => formatDate(data)},
                {data: "date_of_loss", title: "Date of Loss", render: (data) => formatDate(data)},
                {data: "handler", title: "Handler"},
                {data: "branch", title: "Branch"},
                {data: "sum_insured", title: "Sum Insured", render: (data) => formatNumberWithCommas(data)},
                {data: "sub_status", title: "Sub-status"},
                {data: "amount_paid", title: "Amount Paid", render: (data) => formatNumberWithCommas(data)},
                {data: "id", title: "claim_id", visible: false}
            ],

            autoWidth: false,
            columnDefs: [
                { targets: 0, width: "15%" }, //Client
                { targets: 1, width: "18%" }, //Category
                { targets: 2, width: "10%" }, //Underwriter
                { targets: 3, width: "10%" }, //Intimation Date
                { targets: 4, width: "10%" }, //Date of Loss
                { targets: 5, width: "8%" }, //Handler
                { targets: 6, width: "10%" }, //Branch
                { targets: 7, width: "9%" }, //Sum Insured
                { targets: 8, width: "10%" }, //Sub Status
                { targets: 9, width: "10%" }, //Amount Paid

            ],

            scrollCollapse: true,
            scrollX: true,
            scrollY: "45dvh",
            searchDelay: 200,
            pageLength: 50,
            lengthMenu: [50, 70, 100],
            paging: true,
            order: [[3, "desc"]],

            initComplete: function(){
                $('#closed-claims-table tbody').removeClass("is-skeleton");
                this.api().columns.adjust();
            },
        });

        $('#closed-claims-search').on('keyup change', function () {
            const inputElement = this;

            clearTimeout(searchTimeout);

            searchTimeout = setTimeout(() => {
                table.search(inputElement.value).draw()}, 300);

            }
        );
        
        $('#closed-claims-sub-status-filter, #closed-claims-category-filter, #closed-claims-underwriter-filter, #closed-claims-handler-filter, #closed-claims-branch-filter').on(
            'change', function(){
                table.draw();
            }
        );
       
        return table;
    }

    function closedClaimsRowEventListener(){
      const captureTableBody = function (){
            if($.fn.DataTable.isDataTable('#closed-claims-table')){
                return $('#closed-claims-table tbody');
            } else{ return; }
        }

        const tableBody = captureTableBody();

        
        tableBody.on('dblclick', 'tr', async function(){
        const table = $('#closed-claims-table').DataTable();
        const rowData = table.row(this).data();
        if(!rowData){ return; }

        const claim_id = rowData.id;
        const claim_category = rowData.category;
        
        const url = `/Home/api/closed-claims-details-one/${decodeURIComponent(claim_id)}/${decodeURIComponent(claim_category)}/`
        try{
            loadingDialog.showModal(); //Show the spinner as we wait the backed fetch (in case of delayals)
            const response = await fetch(url);
             if(!response.ok){
                throw new Error(`Failed to load data for claim ${claim_id}: ${response.status}`);
             }

             const data = await response.json();

             loadingDialog.close(); //Remove the spinner after the data is fetched from the backend

             if(claim_category == "Motor"){
              populateMotorDetailsDialog(rowData, data);
             }
             else if(claim_category == "Non_Motor"){
              populateNonMotorDetailsDialog(rowData, data);
             }
             else if (claim_category == "Credit_Life"){
              populateCreditLifeDetailsDialog(rowData, data);
             }
             else {
              alert("Invalid category!");
              return;
             }

            //  alert(data);
             console.table(data);


        } catch(err){
            alert(`Failed to load the details for claim number ${claim_id}`);
            console.log(err)
        }

        // alert(`dblclick worked and the id is ${claim_id}, and category is ${claim_category}`);
    });
    }

    function initPendingClaimsTable(){
        if($.fn.DataTable.isDataTable("#pending-claims-table")){
            $('#pending-claims-table').DataTable().clear().destroy();
        }

        const table = $("#pending-claims-table").DataTable({
            serverSide: true,
            processing: true,
            ajax: {
                url: "/Home/api/pending-claims/",
                type: "POST",
                data: function(d){
                    d.subStatus = $('#pending-claims-sub-status-filter').val();
                    d.branch = $('#pending-claims-branch-filter').val();
                    d.handler = $('#pending-claims-handler-filter').val();
                    d.underwriter = $('#pending-claims-underwriter-filter').val();
                    d.category = $('#pending-claims-category-filter').val();
                    return d;
                },
                beforeSend: function(xhr){
                    xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                    $('#pending-claims-table tbody').addClass('is-loading');
                },
                dataSrc: function(json){
                    //source/capture the total pending claims number from here
                    $('#pending-claims-count').text(formatNumberWithCommas(json.recordsTotal));
                    return json.data;
                },
                complete: function(json){
                    $('#pending-claims-table tbody').removeClass('is-loading');
                    if($.fn.DataTable.isDataTable('#pending-claims-table')){
                        $('#pending-claims-table').DataTable().columns.adjust();
                    }
                },
                error: function(xhr){
                    console.error("Claims fetch failed:", xhr.responseText);
                    alert("Could not load claims. Kindly check your network and try again");
                }

            },//end of ajax

            layout: {
                topStart: "pageLength",
                topEnd: null,
                bottomStart: "info",
                bottomEnd: "paging"
            },

            columns: [
                {data: "name_of_insured", title: "Client"},
                {data: "category", title: "Category",  render:(data)=> changeCategoriesToUserFriendly(data)},
                {data: "underwriter", title: "Underwriter"},
                {data: "intimation_date", title: "Intimation Date", render: (data) => formatDate(data)},
                {data: "date_of_loss", title: "Date of Loss", render: (data) => formatDate(data)},
                {data: "days_pending", title: "Days Pending"},
                {data: "documented", title: "Documented?", render: (data) => changeBooleanToYesOrNo(data)},
                {data: "date_fully_documented", title: "Date Documented", render:(data)=> formatDate(data)},
                {data: "handler", title: "Handler"},
                {data: "branch", title: "Branch"},
                {data: "sub_status", title: "Sub-status"},
                {data: "sum_insured", title: "Sum Insured", render: (data) => formatNumberWithCommas(data)},
                {data: "id", title: "claim_id", visible: false}
                
            ],

            autoWidth: false,
            columnDefs: [
                { targets: 0, width: "15%" }, //Client
                { targets: 1, width: "8%" }, //Category
                { targets: 2, width: "10%" }, //Underwriter
                { targets: 3, width: "8%" }, //Intimation Date
                { targets: 4, width: "8%" }, //Date of Loss
                { targets: 5, width: "8%" }, //Days Pending
                { targets: 6, width: "7%" }, //Documented
                { targets: 7, width: "10%" }, //Date Fully Documented
                { targets: 8, width: "8%" }, //Handler
                { targets: 9, width: "10%" }, //Branch
                { targets: 10, width: "10%" }, //Sub-status
                { targets: 11, width: "8%" }, //Sum Insured

            ],

            scrollCollapse: true,
            scrollX: true,
            scrollY: "45dvh",
            searchDelay: 200,
            pageLength: 50,
            lengthMenu: [50, 70, 100],
            paging: true,
            order: [[4, "desc"]],

            initComplete: function(){
                $('#pending-claims-table tbody').removeClass("is-skeleton");
                this. api().columns.adjust();
            },
        });

        $('#pending-claims-search').on('keyup change', function(){
            const inputElement = this;

            clearTimeout(searchTimeout);

            searchTimeout = setTimeout(() => {
                table.search(inputElement.value).draw()}, 300);

            });
        
        $('#pending-claims-sub-status-filter, #pending-claims-category-filter, #pending-claims-underwriter-filter, #pending-claims-handler-filter, #pending-claims-branch-filter').on(
            'change', function(){
                table.draw();
            }
        );
       
        return table;
    }

    function pendingClaimsRowEventListener(){
      const captureTableBody = function (){
            if($.fn.DataTable.isDataTable('#pending-claims-table')){
                return $('#pending-claims-table tbody');
            } else{ return; }
        }

        const tableBody = captureTableBody();

        
        tableBody.on('dblclick', 'tr', async function(){
        const table = $('#pending-claims-table').DataTable();
        const rowData = table.row(this).data();
        if(!rowData){ return; }

        const claim_id = rowData.id;
        const claim_category = rowData.category;
        
        const url = `/Home/api/pending-claims-details-one/${decodeURIComponent(claim_id)}/${decodeURIComponent(claim_category)}/`
        try{
            loadingDialog.showModal(); //Show the spinner as we wait the backed fetch (in case of delayals)

            const response = await fetch(url);
             if(!response.ok){
                throw new Error(`Failed to load data for claim ${claim_id}: ${response.status}`);
             }

             const data = await response.json();

             loadingDialog.close(); //Remove the spinner after the data is fetched from the backend

             if(claim_category == "Motor"){
              populateMotorDetailsDialog(rowData, data);
             }
             else if(claim_category == "Non_Motor"){
              populateNonMotorDetailsDialog(rowData, data);
             }
             else if (claim_category == "Credit_Life"){
              populateCreditLifeDetailsDialog(rowData, data);
             }
             else {
              alert("Invalid category!");
              return;
             }

            //  alert(data);
             console.table(data);


        } catch(err){
            alert(`Failed to load the details for claim number ${claim_id}`);
            console.log(err)
        }

        // alert(`dblclick worked and the id is ${claim_id}, and category is ${claim_category}`);
    });
    }

    $(document).ready(function (){
        $('#total-claims-table tbody'). addClass('is-skeleton');
        $('#closed-claims-table tbody'). addClass('is-skeleton');
        $('#pending-claims-table tbody'). addClass('is-skeleton');
        initTotalClaimsTable();
        totalClaimsRowEventListener(); //NB: add the listener to the table after it has fully loaded or you'll get an 'undefined' error!
        initClosedClaimsTable();
        closedClaimsRowEventListener(); //NB: add the listener to the table after it has fully loaded or you'll get an 'undefined' error!
        initPendingClaimsTable();
        pendingClaimsRowEventListener(); //NB: add the listener to the table after it has fully loaded or you'll get an 'undefined' error!

        const cancelDialogBtns = [
        elements.motorDialogCloseBtn, elements.motorDialogCloseXBtn,
        elements.nonMotorDialogCloseBtn, elements.nonMotorDialogCloseXBtn,
        elements.creditLifeDialogCloseBtn, elements.creditLifeDialogCloseXBtn,
      ]

    cancelDialogBtns.forEach(btn => {
      btn.addEventListener('click', function () {
        // Find the parent dialog of the clicked button
        const dialog = btn.closest('dialog');

        if (dialog && dialog.open) {
          // Reset scroll position if needed
          const body = dialog.querySelector('.dialog-body');
          if (body) body.scrollTop = 0;

          dialog.close();

          
          }
        });
      });

    });

    function downloadTotalClaims(){
        const statusFilter = document.getElementById('total-claims-status-filter');
        const branchFilter = document.getElementById('total-claims-branch-filter');
        const handlerFilter = document.getElementById('total-claims-handler-filter');
        const underwriterFilter = document.getElementById('total-claims-underwriter-filter');
        const categoryFilter = document.getElementById('total-claims-category-filter');

        filteringPayload = {
            "statusFilter": statusFilter.value ? statusFilter.value : '',
            "handlerFilter": handlerFilter.value ? handlerFilter.value : '',
            "underwriterFilter": underwriterFilter.value ? underwriterFilter.value : '',
            "categoryFilter": categoryFilter.value ? categoryFilter.value : '',
            "branchFilter": branchFilter.value ? branchFilter.value : ''
        }

        $.ajax({
            url: "/Home/api/download-total-claims/",
            method: "POST",
            //dataType: "xml", //the kind of data we're expecting from the server
            xhrFields: { responseType: "blob" },
            data: JSON.stringify(filteringPayload),
            contentType: "application/json",
            cache: false, //very important to prevent the browser from dowloading older data
            headers: {"X-CSRFToken": getCookie("csrftoken")},
            beforeSend: function(){
                loadingDialog.showModal();
            },
            complete: function(){
                loadingDialog.close();
                filteringPayload = {};
            },
            success: function(blob, textStatus, xhr){
                // Read the filename the server chose
                let filename = "Claims_report.xlsx"; // fallback
                const disposition = xhr.getResponseHeader("Content-Disposition");
                if (disposition) {
                    const match = disposition.match(/filename="?([^";']+)"?/i);
                    if (match) filename = match[1];
                }

                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            
            },
            error: function(xhr){
                console.error("Failed to fetch data for downloading:", xhr.responseText);
                alert("Failed to fetch the data to download!");
            }
        })
    }
    
    function downloadClosedClaims(){
        const branchFilter = document.getElementById('closed-claims-branch-filter');
        const handlerFilter = document.getElementById('closed-claims-handler-filter');
        const underwriterFilter = document.getElementById('closed-claims-underwriter-filter');
        const categoryFilter = document.getElementById('closed-claims-category-filter');
        const subStatusFIlter = document.getElementById('closed-claims-sub-status-filter');

        filteringPayload = {
            "branchFilter" : branchFilter.value? branchFilter.value : "",
            "handlerFilter": handlerFilter.value? handlerFilter.value : "",
            "underwriterFilter": underwriterFilter.value? underwriterFilter.value : "",
            "categoryFilter" : categoryFilter.value? categoryFilter.value : "",
            "subStatusFilter": subStatusFIlter.value? subStatusFIlter.value : "",
            
        }


        $.ajax({
            url: "/Home/api/download-closed-claims/",
            type: "POST",
            headers: {"X-CSRFToken": getCookie("csrftoken")},
            data: JSON.stringify(filteringPayload),
            contentType: "application/json",
            xhrFields: { responseType: "blob" },
            cache: false,                           //very important to prevent the browser from dowloading older data
            beforeSend: function(){
                loadingDialog.showModal();
            },
            success: function(blob, textStatus, xhr){
                let filename = "Closed_claims_report.xlsx";
                const disposition = xhr.getResponseHeader("Content-Disposition");
                if(disposition){
                    match = disposition.match(/filename="?([^";"']+)"?/i);
                    if(match){filename = match[1];}
                    
                }

                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            },
            error: function(xhr){
                alert("Failed to fetch the data to download!");
                console.log("Failed to load the data for downloading: " + xhr.responseText)
            },
            complete: function(){
                loadingDialog.close();
                filteringPayload = {};
            }

        });

    }

    function downloadPendingClaims(){
        const branchFilter = document.getElementById('pending-claims-branch-filter');
        const handlerFilter = document.getElementById('pending-claims-handler-filter');
        const underwriterFilter = document.getElementById('pending-claims-underwriter-filter');
        const categoryFilter = document.getElementById('pending-claims-category-filter');
        const subStatusFIlter = document.getElementById('pending-claims-sub-status-filter');

        filteringPayload = {
            "branchFilter" : branchFilter.value? branchFilter.value : "",
            "handlerFilter": handlerFilter.value? handlerFilter.value : "",
            "underwriterFilter": underwriterFilter.value? underwriterFilter.value : "",
            "categoryFilter" : categoryFilter.value? categoryFilter.value : "",
            "subStatusFilter": subStatusFIlter.value? subStatusFIlter.value : "",
            
        }


        $.ajax({
            url: "/Home/api/download-pending-claims/",
            type: "POST",
            headers: {"X-CSRFToken": getCookie("csrftoken")},
            data: JSON.stringify(filteringPayload),
            contentType: "application/json",
            xhrFields: { responseType: "blob" },
            cache: false,                           //very important to prevent the browser from dowloading older data
            beforeSend: function(){
                loadingDialog.showModal();
            },
            success: function(blob, textStatus, xhr){
                let filename = "Pending_claims_report.xlsx";
                const disposition = xhr.getResponseHeader("Content-Disposition");
                if(disposition){
                    match = disposition.match(/filename="?([^";"']+)"?/i);
                    if(match){filename = match[1];}
                    
                }

                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            },
            error: function(xhr){
                alert("Failed to fetch the data to download!");
                console.log("Failed to load the data for downloading: " + xhr.responseText)
            },
            complete: function(){
                loadingDialog.close();
                filteringPayload = {};
            }

        });

    }


    totalClaimsDownloadBtn.addEventListener('click', function(){
        downloadTotalClaims();
        
    });

    closedClaimsDownloadBtn.addEventListener('click', function(){
        downloadClosedClaims();
    });

    pendingClaimsDownloadBtn.addEventListener('click', function(){
        downloadPendingClaims();
    });


    function populateMotorDetailsDialog(rowData, data){
      elements.motorDialog.showModal();

      elements.motorClaimId.textContent = rowData.id;
      elements.motorNameOfInsured.value = rowData.name_of_insured;
      elements.motorIntimationDate.value = formatDate(rowData.intimation_date);
      elements.motorDateOfLoss.value = formatDate(rowData.date_of_loss);
      elements.motorCircumstance.value = data.circumstance;
      elements.motorSumInsured.value = formatNumberWithCommas(rowData.sum_insured);
      elements.motorRegistrationNumber.value = data.registration_number;
      elements.motorMotorClass.value = data.motor_class;
      elements.motorAssessor.value = data.assessor;
      elements.motorUnderwriter.value = rowData.underwriter;
      elements.motorBranch.value = rowData.branch;
      elements.motorHandler.value = rowData.handler;
      elements.motorStatus.value = data.status;
      elements.motorStatusBadge.className=""
      if(data.status == "Pending"){
        elements.motorStatusBadge.classList.add("badge-pending");
        elements.motorStatusBadge.textContent = "Pending";
      }
      else if(data.status == "Closed"){
        elements.motorStatusBadge.classList.add("badge-closed");
        elements.motorStatusBadge.textContent = "Closed";
      }
      else{
        elements.motorStatusBadge.textContent = data.status || "-";
      }
      elements.motorSubStatus.value = data.sub_status;
      elements.motorDocumented.value = data.documented;
      elements.motorDateFullyDocumented.value = formatDate(data.date_fully_documented);
      elements.motorDateDvIssued.value = formatDate(data.date_dv_issued);
      elements.motorDateDvReturned.value = formatDate(data.date_dv_returned);
      elements.motorDvAmount.value = formatNumberWithCommas(data.dv_amount);
      elements.motorAmountPaid.value = formatNumberWithCommas(data.amount_paid);
      elements.motorClosureDate.value = formatDate(data.closure_date);
      elements.motorTatDv.value = data.tat_dv;
      elements.motorTatCl.value = data.tat_cl;
      elements.motorDaysPending.value = data.days_pending;
      elements.motorNotes.value = data.notes;
      elements.motorCreatedAt.textContent = formatDate(data.created_at);
      elements.motorUpdatedAt.textContent = formatDate(data.updated_at);
      // elements.motorMotorClass.value = data.motor_class;
      data = {};
      rowData = {};
      

    }

    function populateNonMotorDetailsDialog(rowData, data){
      elements.nonMotorDialog.showModal();

      elements.nonMotorClaimId.textContent = rowData.id;
      elements.nonMotorNameOfInsured.value = rowData.name_of_insured;
      elements.nonMotorIntimationDate.value = formatDate(rowData.intimation_date);
      elements.nonMotorDateOfLoss.value = formatDate(rowData.date_of_loss);
      elements.nonMotorCircumstance.value = data.circumstance;
      elements.nonMotorSumInsured.value = formatNumberWithCommas(rowData.sum_insured);
      elements.nonMotorCoverType.value = data.cover_type;
      elements.nonMotorUnderwriter.value = rowData.underwriter;
      elements.nonMotorBranch.value = rowData.branch;
      elements.nonMotorHandler.value = rowData.handler;
      elements.nonMotorStatus.value = data.status;
      elements.nonMotorStatusBadge.className=""
      if(data.status == "Pending"){
        elements.nonMotorStatusBadge.classList.add("badge-pending");
        elements.nonMotorStatusBadge.textContent = "Pending";
      }
      else if(data.status == "Closed"){
        elements.nonMotorStatusBadge.classList.add("badge-closed");
        elements.nonMotorStatusBadge.textContent = "Closed";
      }
      else{
        elements.nonMotorStatusBadge.textContent = data.status || "-";
      }
      elements.nonMotorSubStatus.value = data.sub_status;
      elements.nonMotorDocumented.value = data.documented;
      elements.nonMotorDateFullyDocumented.value = formatDate(data.date_fully_documented);
      elements.nonMotorDateDvIssued.value = formatDate(data.date_dv_issued);
      elements.nonMotorDvAmount.value = formatNumberWithCommas(data.dv_amount);
      elements.nonMotorDateDvReturned.value = formatDate(data.date_dv_returned);
      elements.nonMotorAmountPaid.value = formatNumberWithCommas(data.amount_paid);
      elements.nonMotorClosureDate.value = formatDate(data.closure_date);
      elements.nonMotorTatDv.value = data.tat_dv;
      elements.nonMotorTatCl.value = data.tat_cl;
      elements.nonMotorDaysPending.value = data.days_pending;
      elements.nonMotorNotes.value = data.notes;
      elements.nonMotorCreatedAt.textContent = formatDate(data.created_at);
      elements.nonMotorUpdatedAt.textContent = formatDate(data.updated_at);
      data = {};
      rowData = {};
      

    }

    function populateCreditLifeDetailsDialog(rowData, data){
      elements.creditLifeDialog.showModal();

      elements.creditLifeClaimId.textContent = rowData.id;
      elements.creditLifeNameOfInsured.value = rowData.name_of_insured;
      elements.creditLifeIntimationDate.value = formatDate(rowData.intimation_date);
      elements.creditLifeDateOfLoss.value = formatDate(rowData.date_of_loss);
      elements.creditLifeCircumstance.value = data.circumstance;
      elements.creditLifeSumInsured.value = formatNumberWithCommas(rowData.sum_insured);
      elements.creditLifeClaimTrigger.value = data.claim_trigger;
      elements.creditLifeUnderwriter.value = rowData.underwriter;
      elements.creditLifeBranch.value = rowData.branch;
      elements.creditLifeHandler.value = rowData.handler;
      elements.creditLifeStatus.value = data.status;
      elements.creditLifeStatusBadge.className=""
      if(data.status == "Pending"){
        elements.creditLifeStatusBadge.classList.add("badge-pending");
        elements.creditLifeStatusBadge.textContent = "Pending";
      }
      else if(data.status == "Closed"){
        elements.creditLifeStatusBadge.classList.add("badge-closed");
        elements.creditLifeStatusBadge.textContent = "Closed";
      }
      else{
        elements.creditLifeStatusBadge.textContent = data.status || "-";
      }
      elements.creditLifeSubStatus.value = data.sub_status;
      elements.creditLifeDocumented.value = data.documented;
      elements.creditLifeDateFullyDocumented.value = formatDate(data.date_fully_documented);
      elements.creditLifeDateDvIssued.value = formatDate(data.date_dv_issued);
      elements.creditLifeDvAmount.value = formatNumberWithCommas(data.dv_amount);
      elements.creditLifeDateDvReturned.value = formatDate(data.date_dv_returned);
      elements.creditLifeAmountPaid.value = formatNumberWithCommas(data.amount_paid);
      elements.creditLifeClosureDate.value = formatDate(data.closure_date);
      elements.creditLifeTatDv.value = data.tat_dv;
      elements.creditLifeTatCl.value = data.tat_cl;
      elements.creditLifeDaysPending.value = data.days_pending;
      elements.creditLifeNotes.value = data.notes;
      elements.creditLifeCreatedAt.textContent = formatDate(data.created_at);
      elements.creditLifeUpdatedAt.textContent = formatDate(data.updated_at);
      data = {};
      rowData = {};

    }