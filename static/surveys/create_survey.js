var num_questions = 0;
//let response_types = ['Text', 'Text-Long', 'Likert', 'Options-Single', 'Options-Multi'];
let response_types = [];
$('#response_types > div.rt').each(function(index) {
    let r = {};
    r['id'] = $(this).find('div.rt_id').text();
    r['name'] = $(this).find('div.rt_name').text();
    response_types.push(r);
});
console.log(response_types);

$('#add-question').click(function() { 
    num_questions++;
    let id_prefix = "question-" + num_questions + "-";
    
    let q_container = $('<div></div>').attr('id', id_prefix + 'container');
    
    //Create Question header
    var header_row = $('<div></div>').addClass('row me-1');
    var header = $('<h3></h3>').text('Question ' + num_questions).addClass('col-11 question-header');
    var header_remove = $('<button></button>').attr('type', 'button').addClass('col-1 btn btn-danger').text('Remove');
    header_row.append(header).append(header_remove);
    q_container.append(header_row).append($('<br>'));

    // Create "Question text" input
    var txt_label = $('<label></label>').addClass('form-label').text('Question text').attr("for", id_prefix + "text");
    var txt_input = $('<input>').attr('type', 'text').addClass('form-control').attr("name", id_prefix + "text").attr("id", id_prefix + "text").attr('required', 'true');
    var txt_div = $('<div></div>').addClass('mb-3');
    txt_div.append(txt_label).append(txt_input);
    q_container.append(txt_div);
    
    // Create "Response type" input
    var typ_label = $('<label></label>').addClass('form-label').text('Response type').attr("for", id_prefix + "response_type");
    var typ_input = $('<select></select>').addClass('form-select').attr("name", id_prefix + "response_type").attr("id", id_prefix + "response_type");
    response_types.forEach(function(x) {
        option = $('<option></option>').attr('value', x['id']).text(x['name']);
        typ_input.append(option);
    });
    var typ_div = $('<div></div>').addClass('mb-3');
    typ_div.append(typ_label).append(typ_input);
    q_container.append(typ_div);
    
    // Create "Required" input
    var req_label = $('<label></label>').addClass('form-label').text('Response required').attr("for", id_prefix + "required");
    var req_input = $('<input>').attr('type', 'checkbox').addClass('form-check-input').attr("name", id_prefix + "required").attr("id", id_prefix + "required");
    var req_div = $('<div></div>').addClass('mb-3 form-check');
    req_div.append(req_label).append(req_input);
    q_container.append(req_div);
    
    // Create "Add option" button
    var opt_container = $('<div></div>').attr("id", id_prefix + "options-container").addClass('d-none');
    var opt_list = $('<div></div>').attr('id', id_prefix + "options-list");
    var opt_div = $('<div></div>').addClass('mb-3');
    var opt_button = $('<button></button>').attr("type", "button").addClass("btn btn-secondary").text("Add option").attr('id', id_prefix + "add-option");
    opt_container.append(opt_list).append(opt_div.append(opt_button));
    q_container.append(opt_container);
    
    // Add line to separate Questions
    q_container.append($('<hr>'));
    
    $('#questions-container').append(q_container);
    
    // Add On Click event to the Remove Question button.
    header_remove.click(function() {
        //alert('remove question button clicked');
        $(this).parent().parent().remove();
        num_questions--;
        $("#questions-container h3.question-header").each(function(index) {
            console.log(index);
            $(this).text('Question ' + (index + 1));
        });
    });
    
    // Add On Change event to response type, which will show the options section if the response type needs options to be defined.
    // The options section will be hidden if the response type does not use user-defined options.
    $("#" + id_prefix + "response_type").change(function() {
        if( $(this).val() == "4" || $(this).val() == "5") {
            $("#" + id_prefix + "options-container").removeClass('d-none');
            $("#" + id_prefix + "options-container input").each(function(index) {
                $(this).removeAttr("disabled");
            });
        }
        else {
            $("#" + id_prefix + "options-container").addClass('d-none');
            $("#" + id_prefix + "options-container input").each(function(index) {
                $(this).attr("disabled", "disabled");
            });
        }
    });
    
    
    // Add On Click event to the "Add option" button
    $("#" + id_prefix + "add-option").click(function() {
        let num_options = $("#" + id_prefix + "options-list input").length
        let option_num = num_options + 1;
        
        let option_div = $('<div></div>').addClass('mb-3');
        let option_row = $('<div></div>').addClass('row me-1 mb-1');
        let option_label = $('<label></label>').attr('for', id_prefix + "option-" + option_num).text('Option ' + option_num).addClass('form-label col-11 fw-bold');
        let option_remove = $('<button></button>').attr('type', 'button').text('Remove').addClass('btn btn-danger col-1');
        let option_input = $('<input>').attr('type', 'text').attr('name', id_prefix + "option-" + option_num).attr('id', id_prefix + "option-" + option_num).addClass('form-control');
        option_row.append(option_label).append(option_remove);
        $("#" + id_prefix + "options-list").append(option_div.append(option_row).append(option_input));
        
        // Add On Click event to the new option's "Remove" button
        option_remove.click(function() {
            console.log($(this).parent().parent().remove());
            let i = 1;
            $("#" + id_prefix + "options-list label").each(function(index) {
                console.log(index + ": " + $(this));
                console.log($(this));
                $(this).attr('for', id_prefix + 'option-' + i).text('Option ' + i);
                i++;
            });
            i = 1;
            $("#" + id_prefix + "options-list input").each(function(index) {
                console.log(index + ": " + $(this));
                console.log($(this));
                $(this).attr('name', id_prefix + 'option-' + i).attr('id', id_prefix + 'option-' + i);
                i++;
            });
        });
    });
});