$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#inventory_id").val(res.id);
        $("#inventory_name").val(res.name);
        $("#inventory_quantity").val(res.quantity);
        $("#inventory_restock_level").val(res.restock_level);
        if (res.condition == "NEW") {
            $("#inventory_condition").val("NEW");
        } else if(res.condition == "OPEN_BOX") {
            $("#inventory_condition").val("OPEN_BOX");
        } else if(res.condition == "USED") {
            $("#inventory_condition").val("USED");
        }
        if (res.restocking_available == true) {
            $("#inventory_restocking_available").val("true");
        } else {
            $("#inventory_restocking_available").val("false");
        }
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#inventory_name").val("");
        $("#inventory_quantity").val("");
        $("#inventory_restock_level").val("");
        $("#inventory_condition").val("");
        $("#inventory_restocking_available").val("");
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Inventory
    // ****************************************

    $("#create-btn").click(function () {

        let name = $("#inventory_name").val();
        let quantity = $("#inventory_quantity").val();
        let restock_level = $("#inventory_restock_level").val();
        let condition = $("#inventory_condition").val();
        let restocking_available = $("#inventory_restocking_available").val() == "true";

        let data = {
            "name": name,
            "quantity": quantity,
            "restock_level": restock_level,
            "condition": condition,
            "restocking_available": restocking_available
        };

        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "POST",
            url: "/api/inventories",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });


    // ****************************************
    // Update a Inventory
    // ****************************************

    $("#update-btn").click(function () {

        let inventory_id = $("#inventory_id").val();
        let name = $("#inventory_name").val();
        let quantity = $("#inventory_quantity").val();
        let restock_level = $("#inventory_restock_level").val();
        let condition = $("#inventory_condition").val();
        let restocking_available = $("#inventory_restocking_available").val() == "true";

        let data = {
            "name": name,
            "quantity": quantity,
            "restock_level": restock_level,
            "condition": condition,
            "restocking_available": restocking_available
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
                type: "PUT",
                url: `/api/inventories/${inventory_id}`,
                contentType: "application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Retrieve a Inventory
    // ****************************************

    $("#retrieve-btn").click(function () {

        let inventory_id = $("#inventory_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/api/inventories/${inventory_id}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Delete a Inventory
    // ****************************************

    $("#delete-btn").click(function () {

        let inventory_id = $("#inventory_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/api/inventories/${inventory_id}`,
            contentType: "application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Inventory has been Deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#inventory_id").val("");
        $("#flash_message").empty();
        clear_form_data()
    });

    // ****************************************
    // Search for a Inventory
    // ****************************************

    $("#search-btn").click(function () {

        let name = $("#inventory_name").val();
        let quantity = $("#inventory_quantity").val();
        let restock_level = $("#inventory_restock_level").val();
        let condition = $("#inventory_condition").val();
        let restocking_available = $("#inventory_restocking_available").val() == "true";

        let queryString = ""

        if (name) {
            queryString += 'name=' + name
        }
        if (quantity) {
            if (queryString.length > 0) {
                queryString += '&quantity=' + quantity
            } else {
                queryString += 'quantity=' + quantity
            }
        }
        if (restock_level) {
            if (queryString.length > 0) {
                queryString += '&restock_level=' + restock_level
            } else {
                queryString += 'restock_level=' + restock_level
            }
        }
        if (condition) {
            if (queryString.length > 0) {
                queryString += '&condition=' + condition
            } else {
                queryString += 'condition=' + condition
            }
        }
        if (restocking_available) {
            if (queryString.length > 0) {
                queryString += '&restocking_available=' + restocking_available
            } else {
                queryString += 'restocking_available=' + restocking_available
            }
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/api/inventories?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-1">ID</th>'
            table += '<th class="col-md-4">Name</th>'
            table += '<th class="col-md-4">Quantity</th>'
            table += '<th class="col-md-3">Restock Level</th>'
            table += '<th class="col-md-3">Condition</th>'
            table += '<th class="col-md-3">Restocking Available</th>'
            table += '</tr></thead><tbody>'
            let firstInventory = "";
            for(let i = 0; i < res.length; i++) {
                let inventory = res[i];
                table +=  `<tr id="row_${i}"><td>${inventory.id}</td><td>${inventory.name}</td><td>${inventory.quantity}</td><td>${inventory.restock_level}</td><td>${inventory.condition}</td><td>${inventory.restocking_available}</td></tr>`;
                if (i == 0) {
                    firstInventory = inventory;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            if (firstInventory != "") {
                update_form_data(firstInventory)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Start Restocking a Inventory
    // ****************************************

    $("#start_restocking-btn").click(function () {

        let inventory_id = $("#inventory_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/api/inventories/${inventory_id}/start_restock`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message("http status:"+res.status)
        });

    });

    $("#stop_restocking-btn").click(function () {

        let inventory_id = $("#inventory_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/api/inventories/${inventory_id}/stop_restock`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message("http status:"+res.status)
        });

    });

})
