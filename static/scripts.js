// Execute when the DOM is fully loaded
$(document).ready(function() {
    // update all sum and total value in tables
    for (let i = 1; i < 5; i++) {
        sum(i);
    }

    // add listener for every new_item button
    add_new_item("button[id^=new_row]");

    // add listener for every delet button
    delete_item("button[name=del_item]");

    // add listener for every delet button
    done("button[name=done]");

    // add edit listener for every value
    edit_item();

});

// add new row to the table
function add_new_item(button) {
    // variable for current table object
    let cur_table;

    // when user click on the button (Add)
    $(button).click(function() {

        // check whether previously created input field
        if ($("tr[name=cur_value]").length == 0) {

            // find out the "id" of the table to which the user adds the value
            cur_table = $(this).closest(".column").find("table").first();

            // invite user to enter values for new item
            cur_table.children("tbody").append(
                `<tr name="cur_value">
                    <td name="td_1" colspan=3>
                        <input autocomplete="off" type="text" name="coment"
                    </td>
                    <td name="td_2">
                        <input autocomplete="off" type="number" min=0 name="cash"
                    </td>
                </tr>`
            );

            // after creating the input field, focus on its first cell
            $('input[name=coment]').focus();
        } else {
            // if input field is created
            return false;
        }

        // remove inpute field
        $("input[name=coment], input[name=cash]").keydown(function(eventObject) {
            if (eventObject.which == 27) {
                $("tr[name=cur_value]").remove();
            }
        });

        // focus transfer by pressing enter at first cell
        $("input[name=coment]").keydown(function(eventObject) {
            if (eventObject.which == 13) {
                $('input[name=cash]').focus();
            }
        });

        // sending data by pressing enter in the second cell
        $("input[name=cash]").keydown(function(eventObject) {
            if (eventObject.which == 13) {
                // values entered by the user
                let cash = $("input[name=cash]")[0].value;
                let coment = $("input[name=coment]")[0].value;

                // check cash value
                if (cash < 0 || cash > 999999 || cash == "" || coment == "") {
                    alert("No way!");
                    $("input[name=cash]")[0].value = "";
                    return false;
                }

                // preparing data for sending to the server
                let new_item = {
                    item: coment,
                    cash: cash,
                    table: $(cur_table).attr('id')
                };
                // remove inpute field
                $("tr[name=cur_value]").remove();

                // request with data to the server
                $.post("/newItem", new_item, function(data, textStatus, jqXHR) {
                    // html - text with a new item for the current table
                    let content =
                        `<tr id=${+data["item_id"]}>
                            <td class="button_block">
                                <button type="button" name="done-temp" class="btn btn-outline-info btn-circle">✓</button>
                            </td>
                            <td name="td_1">
                                <div class="edit" contenteditable>${new_item["item"]}</div>
                            </td>
                            <td class="button_block">
                                <button type="button" name="del_item-temp" class="btn btn-outline-danger btn-circle">×</button>
                            </td>
                            <td name="td_2">
                                <div class="wraper">
                                <div class="symbol">₴</div>
                                <div class="edit" contenteditable>${new_item["cash"]}
                                </div>
                            </td>
                        </tr>`;

                    // add new item to current table
                    $(cur_table).append(content);

                    // update balance
                    cur_balance(data["cash"]);

                    // editing listener
                    edit_item();

                    // done - button listener
                    $("button[name=done-temp]").unbind("click");
                    done("button[name=done-temp]");

                    // delet - button listener
                    $("button[name=del_item-temp]").unbind("click");
                    delete_item("button[name=del_item-temp]");

                    // update sum and total value in current column
                    let column = $(button).closest(".column").attr('name');
                    sum(column);
                }, "json");
            }
        });
    });
}

// delete row from table
function delete_item(button) {
    // listener of all delete-buttons
    $(button).click(function() {
        // deletion warning
        if (confirm("I swear, I'll remove it!")) {

            // find out current column and row
            let column = $(this).closest(".column").attr('name');
            let row = $(this).closest("tr");

            // preparing data for sending to the server
            let item = {
                // current item_id
                id: row.attr('id'),
                // current cash
                cash: row.find(".edit").last().text()
            };

            // remove current row
            row.remove();

            // update sum and total value in current column
            sum(column);

            // request with data to the server
            $.post("/delete_item", item, function(data, textStatus, jqXHR) {
                // update balance
                cur_balance(data["cash"]);
            }, "json");


        } else {
            // cancel delition
            return false;
        }
    });
}

// edit any cell
function edit_item() {

    // listener of all content-editable element
    $(".edit").keypress(function(eventObject) {
        // prevent the second line
        if (eventObject.which == 13) {
            return false;
        }
    });

    // variables for: current_object, old cell value, new cell value, current item id, current column name
    let obj, oldVal, newVal, id, col;

    // listener of all content-editable element
    $(".edit").focus(function save_edit() {

        // current_object
        obj = $(this);

        // old cell value
        oldVal = obj.text();

        // current column name
        col = obj.closest("td").attr('name');
        // current item id
        id = obj.closest("tr").attr('id');
    }).on("keypress blur", function(eventObject) {
        // sending data to the server by pressing enter or defocusing
        if (eventObject.which == 13) {
            $(this).blur();
        } else if (eventObject.type == 'blur') {
            // new cell value
            newVal = $(this).text();

            // validation of new value
            if (col.slice(-1) == 2 && (newVal <= 0 || isNaN(newVal))) {
                alert("No way!");
                $(this).text(oldVal);
                return false;
            }
            // change check
            else if (oldVal != newVal) {
                // preparing data for sending to the server
                let options = { id: id, newVal: newVal, oldVal: oldVal, col: col };
                // request with data to the server
                $.post("/edit_item", options, function(data, textStatus, jqXHR) {
                    // update balance
                    cur_balance(data["cash"]);
                }, "json");

                // update sum and total value in current column
                let column = $(this).closest(".column").attr('name');
                sum(column);
            }
        }
    });
}

function done(button) {
    $(button).click(function() {

        // current item_id and number of table
        let id = $(this).closest("tr").attr('id');
        let table = $(this).closest("table").attr('id').slice(-1);

        // up tables
        if (table >= 1 && table <= 4) {
            // moving item down
            $(this).closest("tr").appendTo($(`#table${Number(table)+4}`).children("tbody"));
            $.post("/done_or_not", { answer: "true", id: id }, function(data, textStatus, jqXHR) {}, "json");
        }

        // down tables
        else if (table >= 5 && table <= 8) {
            // moving item up
            $(this).closest("tr").appendTo($(`#table${Number(table)-4}`).children("tbody"));
            $.post("/done_or_not", { answer: "false", id: id }, function(data, textStatus, jqXHR) {}, "json");
        }

        // update sum and total value in current column
        let column = $(this).closest(".column").attr('name');
        sum(column);
    });
}

// screen balance update
function cur_balance(current_cash) {
    // check element existence
    if ($("#balance")) {

        // replace the current balance value
        $("#balance").text("Balance: " + current_cash);

        if (Number(current_cash) < 0) {
            // negative balance value is highlighted in red
            $("#balance").get(0).style.color = "red";
            $("#balance").get(0).style.fontWeight = "bold";
        } else {
            // negative balance value is highlighted by normal
            $("#balance").get(0).style.color = null;
            $("#balance").get(0).style.fontWeight = "normal";
        }
    }

}

// update sum and total value
function sum(col_num) {
    // variables for: current_column id, top table, bottom table
    let column, tab_up, tab_down;
    // variables for: sum top table values, bottom table values, both table values
    let sum_up = 0,
        sum_down = 0,
        sum_tot;

    column = $(`div[name=${col_num}]`).find("table[id^=table]");
    tab_up = column.first().find("td[name=td_2]").text().split("₴");
    tab_down = column.last().find("td[name=td_2]").text().split("₴");
    total = column.find("td[name=td_2]").text().split("₴");


    // sum of values in the upper table
    for (let i = 0, len = tab_up.length; i < len; i++) {
        sum_up = sum_up + Number(tab_up[i]);
    }

    // the sum of the values in the bottom table
    for (let i = 0, len = tab_down.length; i < len; i++) {
        sum_down = sum_down + Number(tab_down[i]);
    }
    sum_tot = sum_up + sum_down;

    // replace the values on the page
    $(`div[name=${col_num}]`).find("output[name=up]").text(sum_up);
    $(`div[name=${col_num}]`).find("output[name=down]").text(sum_down);
    $(`div[name=${col_num}]`).find("output[name=total]").text(sum_tot);
}