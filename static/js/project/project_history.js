/**
 * Created by haibin on 14-3-6.
 */

$(document).ready(function(){
    $('#history_table').dataTable({
        "oLanguage": oLanguages,
        "bFilter": false,
        "aLengthMenu": [[10, 25, 50], [10, 25, 50]],
        "iDisplayLength" : 50,
        "aaSorting": [[ 0, "desc" ]],
        "bAutoWidth": true,
        "aoColumns": [
                        { "bSortable": false, "bSearchable": false, "sClass": "center" },
                        { "bSortable": false, "bSearchable": true, "sClass": "center" },
                        { "bSortable": false, "bSearchable": true, "sClass": "center" },
                        { "bSortable": false, "bSearchable": false, "sClass": "center" },
                        { "bSortable": false, "bSearchable": false, "sClass": "center" },
                        { "bSortable": false, "bSearchable": false, "sClass": "center" },
                        { "bSortable": false, "bSearchable": false, "sClass": "center" },
                        { "bSortable": false, "bSearchable": false, "sClass": "center" }
                        ],
        "bProcessing": true,
        "bServerSide": true,
        "bStateSave": true,
        "sAjaxSource": USERS_LIST_JSON_URL,
        "sPaginationType": "full_numbers",
        "bJQueryUI": true,
        "sDom": '<"top"flp>rt<"bottom"i><"clear">'
    });

    $('#sidebar li').removeClass('active');
    $('#bar-history').addClass('active');
})