
$(document).ready(function(){
$("#mytable #checkall").click(function () {
        if ($("#mytable #checkall").is(':checked')) {
            $("#mytable input[type=checkbox]").each(function () {
                $(this).prop("checked", true);
            });

        } else {
            $("#mytable input[type=checkbox]").each(function () {
                $(this).prop("checked", false);
            });
        }
    });

    $("[data-toggle=tooltip]").tooltip();
});


/**
 * Vertically center Bootstrap 3 modals so they aren't always stuck at the top
 */
$(function() {
    function reposition() {
        var modal = $(this),
            dialog = modal.find('.modal-dialog');
        modal.css('display', 'block');

        // Dividing by two centers the modal exactly, but dividing by three
        // or four works better for larger screens.
        dialog.css("margin-top", Math.max(0, ($(window).height() - dialog.height()) / 2));
    }
    // Reposition when a modal is shown
    $('.modal').on('show.bs.modal', reposition);
    // Reposition when the window is resized
    $(window).on('resize', function() {
        $('.modal:visible').each(reposition);
    });
});


/**
 * Circle percent http://bootsnipp.com/snippets/Gq45X
 */
$(function(){
      var $ppc = $('.progress-pie-chart'),
        percent = parseInt($ppc.data('percent')),
        deg = 360*percent/100;
      if (percent > 50) {
        $ppc.addClass('gt-50');
      }
      $('.ppc-progress-fill').css('transform','rotate('+ deg +'deg)');
      $('.ppc-percents span').html(percent+'%');
    });


/**
 * Go to the previous page
 */
function goBack() {
    window.history.back();
}


/**
 * Delete modal, adjust the id of the project into the modal before deleting
 */
$(document).ready(function(){
    $(".delete-modal").click(function(e){
        var projectid = $(this).attr("projectid");
            $("#delete-project").attr("href", "/project/delete/" + projectid);
    e.preventDefault();
    })
});


/**
 *Gestion des tableaux filtrant
 */


$(document).ready(function(){
    $('.filterable .btn-filter').click(function(){
        var $panel = $(this).parents('.filterable'),
        $filters = $panel.find('.filters input'),
        $tbody = $panel.find('.table tbody');
        if ($filters.prop('disabled') == true) {
            $filters.prop('disabled', false);
            $filters.first().focus();
        } else {
            $filters.val('').prop('disabled', true);
            $tbody.find('.no-result').remove();
            $tbody.find('tr').show();
        }
    });

    $('.filterable .filters input').keyup(function(e){
        /* Ignore tab key */
        var code = e.keyCode || e.which;
        if (code == '9') return;
        /* Useful DOM data and selectors */
        var $input = $(this),
        inputContent = $input.val().toLowerCase(),
        $panel = $input.parents('.filterable'),
        column = $panel.find('.filters th').index($input.parents('th')),
        $table = $panel.find('.table'),
        $rows = $table.find('tbody tr');
        /* Dirtiest filter function ever ;) */
        var $filteredRows = $rows.filter(function(){
            var value = $(this).find('td').eq(column).text().toLowerCase();
            return value.indexOf(inputContent) === -1;
        });
        /* Clean previous no-result if exist */
        $table.find('tbody .no-result').remove();
        /* Show all rows, hide filtered ones (never do that outside of a demo ! xD) */
        $rows.show();
        $filteredRows.hide();
        /* Prepend no-result row if all rows are filtered */
        if ($filteredRows.length === $rows.length) {
            $table.find('tbody').prepend($('<tr class="no-result text-center"><td colspan="'+ $table.find('.filters th').length +'">No result found</td></tr>'));
        }
    });
});


/**
 * On/Off button switch
 */
$('#OnOffButton').bootstrapSwitch();

$('#OnOffButton').on('switchChange.bootstrapSwitch', function (){
        var id = $(location).attr('href').split('/').slice(-1)[0];
         $.ajax({
                type: "POST",
                contentType: "application/json; charset=utf-8",
                url: '/project/privacy',
                data: JSON.stringify({id: id}),
                dataType: 'json',
                success: function(response) {
                    console.log(response);
                },
                error: function(error) {
                    console.log(error);
                }
            });
    }
)


/**
  * Add a new project user in the project page
  */
/**
$(document).on('click', '.add-more', function(e){
    e.preventDefault();
    var href_add_user = $('.add-more').attr('href');
    var uid = $("#user").val();
    uid = uid.split(/[\(),]+/)[1];
    var $addto = $("tr:last");
    //var addto = "#project-user";

    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: href_add_user,
        data: JSON.stringify({'uid': uid}),
        dataType: 'json',
        success: function(response) {
            console.log(response);
            var newIn = "<tr><td align='center'><a href='/user/display/" + response['id'] + "'><i class='-alt fa fa-2x fa-user fa-fw'></i></a></td><td><h4><b>"+response['function']+"</b></h4><p>"+response['service']+"</p></td><td><img src='http://pingendo.github.io/pingendo-bootstrap/assets/user_placeholder.png' class='img-circle' width='60'></td><td><h4><b>" + response['firstname'] + " " + response['lastname'] + "</b></h4><a href='mailto:" + response['mail'] + "'>" + response['mail'] + "</a></td><td><h5><b>Last update</b></h5></td><td><a href=''  type='button' class='delete btn btn-sm btn-danger'><i class='glyphicon glyphicon-trash'></i> Delete User</a></td></tr>"
            var newInput = $(newIn);
            var addto = $("tr:last");
            addto.after(newInput);
        },
        error: function(error) {
            console.log(error);
        }
    });
});*/

/**
  * Remove an user project
  */
$(document).on('click', '.delete', function(e){
    e.preventDefault();
    var $button = $(this);
    var href_remove_user = $(this).attr('href');

    $.ajax({
        type: "POST",
        contentType: "application/json; charset=utf-8",
        url: href_remove_user,
        dataType: 'json',
        success: function(response) {
            if(response['is_removed'] == true)
                $button.parent().parent().remove();
        },
        error: function(error) {
            console.log(error);
        }
    });
});

/**
 * Autocomplete input
 */
$(function() {
    var input = $("input#user-input");
    var id = input.attr('name');
    var users = {};
    $.ajax({
    	url: "/project/" + id + "/users",
    	async: false,
    	dataType: 'json',
    	success: function(data) {
    		users = data;
    	}
    });
    input.autocomplete({
        source: [users]
    });
});


$('input#user-input').keydown(function(e) {
    if (e.keyCode == '13') {
        e.preventDefault();
        var input = $('input#user-input')
        var id = input.attr('name');
        var uid = input.val();
        console.log(uid);
        uid = uid.split(/[\(),]+/)[1];

        $.ajax({
            type: "POST",
            contentType: "application/json; charset=utf-8",
            url: '/project/'+ id + '/addUser',
            data: JSON.stringify({'uid': uid}),
            dataType: 'json',
            success: function(response) {
                console.log(response);
                var newIn = "<tr><td align='center'><a href='/user/display/" + response['id'] + "'><i class='-alt fa fa-2x fa-user fa-fw'></i></a></td><td><h4><b>" + response['firstname'] + " " + response['lastname'] + "</b></h4></td><td><h4><b>" + response['function'] + "</b></h4></td><td><h4><b>" + response['service'] + "</td><td><h5><b>Last update</b></h5></td><td><a href='/project/" + id + "/removeUser/" + response['id'] + "'  type='button' class='delete btn btn-sm btn-danger'><i class='glyphicon glyphicon-trash'></i> Delete User</a></td></tr>"
                var newInput = $(newIn);
                var addto = $("tr:last");
                addto.after(newInput);
            },
            error: function(error) {
                console.log(error);
            }
        });
    }
});