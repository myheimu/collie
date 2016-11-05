/**
 * Created by haibin on 14-4-28.
 */

$('#btn_delete_module').bind('click', function() {
    bootbox.dialog({
        'message': 'Are you sure to delete this module?',
        'buttons': {
            'confirm': {
                'label': 'Yes',
                'className': 'btn-danger',
                callback: function() {
                    $.post(
                        '/module/delete',
                        {
                            'module_id': getURLParameter('module_id')
                        },
                        function(r) {
                            if (r.status > 0) {
                                bootbox.dialog({
                                    message: 'delete successfully',
                                    buttons: {
                                        success: {
                                            label: 'OK',
                                            callback: function() {
                                                document.location.href = "/module/index";
                                            }
                                        }
                                    }
                                });
                            } else {
                                alert('delete module failed');
                            }
                        }
                    )
                }
            },
            'cancel': {
                'label': 'No',
                'className': 'btn-default',
                callback: function() {
                    return;
                }
            }
        }
    })

})

$('#btn_update_module').bind('click', function() {
    var moduleId = $('#module_info').attr('module_id');
    var latestVersionId = $('#module_info').attr('latest_version_id');

    $(document).data('modalMode', 'update');
    $(document).data('moduleId', moduleId);
    $(document).data('moduleVersion', latestVersionId);
    $('#newModuleModal').modal({backdrop: 'static'});
})

$('#owner_edit').bind('click', function() {
    var owner = $('#label_owner').text();
    $('#label_owner').hide();
    $('#input_owner').val(owner);
    $('#input_owner').show();
    $('#owner_edit').hide();
    $('#owner_submit').show();
})

$('#owner_submit').bind('click', function() {
    var moduleId = $('#module_info').attr('module_id');
    var owner = $('#input_owner').val();

    $.ajax({
        url: '/module/owner/update',
        type: 'POST',
        data: {
            'module_id': moduleId,
            'owner': owner
        },
        success: function(r) {
            if (r.status > 0) {
                $('#label_owner').text(owner);
                $('#label_owner').show();
                $('#input_owner').hide();
                $('#owner_submit').hide();
                $('#owner_edit').show();
            } else {
                bootbox.alert("Error: " + r.error);
            }
        },
        async: false
    })
})

$('#description_edit').bind('click', function() {
    var description = $('#label_description').text();
    $('#label_description').hide();
    $('#input_description').val(description);
    $('#input_description').show();
    $('#description_edit').hide();
    $('#description_submit').show();
})

$('#description_submit').bind('click', function() {
    var moduleId = $('#module_info').attr('module_id');
    var description = $('#input_description').val();

    $.ajax({
        url: '/module/description/update',
        type: 'POST',
        data: {
            'module_id': moduleId,
            'description': description
        },
        success: function(r) {
            if (r.status > 0) {
                $('#label_description').text(description);
                $('#label_description').show();
                $('#input_description').hide();
                $('#description_submit').hide();
                $('#description_edit').show();
            } else {
                bootbox.alert("Error: " + r.error);
            }
        },
        async: false
    })
})

$('#wiki_link_edit').bind('click', function() {
    var wiki_link = $('#label_wiki_link').attr('href');
    $('#label_wiki_link').hide();
    $('#input_wiki_link').val(wiki_link);
    $('#input_wiki_link').show();
    $('#wiki_link_edit').hide();
    $('#wiki_link_submit').show();
})

$('#wiki_link_submit').bind('click', function() {
    var moduleId = $('#module_info').attr('module_id');
    var wiki_link = $('#input_wiki_link').val();

    $.ajax({
        url: '/module/wiki_link/update',
        type: 'POST',
        data: {
            'module_id': moduleId,
            'wiki_link': wiki_link
        },
        success: function(r) {
            if (r.status > 0) {
                if (wiki_link.length > 60) {
                    $('#label_wiki_link').text(wiki_link.substr(0, 60));
                } else {
                    $('#label_wiki_link').text(wiki_link);
                }
                $('#label_wiki_link').attr('href', wiki_link);
                $('#label_wiki_link').show();
                $('#input_wiki_link').hide();
                $('#wiki_link_submit').hide();
                $('#wiki_link_edit').show();
            } else {
                bootbox.alert("Error: " + r.error);
            }
        },
        async: false
    })
})

$('.btn_version_delete').bind('click', function() {
    if ($('#version_table tbody tr').length <= 1) {
        bootbox.alert('Error: must keep at least 1 version.');
        return;
    }

    var versionId = $(this).attr('version_id');
    bootbox.dialog({
        message: 'Are you sure to delete this version',
        buttons: {
            confirm: {
                label: 'Yes',
                className: 'btn-danger',
                callback: function() {
                    openModal('delete_fade', 'delete_modal');
                    $.ajax({
                            url: '/module/version/delete',
                            type: 'POST',
                            data: {
                                'version_id' : versionId
                            },
                            success: function(r) {
                                if (r.status > 0) {
                                    bootbox.dialog({
                                        message: 'delete successfully',
                                        buttons: {
                                            success: {
                                                label: 'OK',
                                                callback: function() {
                                                    var moduleId = getURLParameter('module_id');
                                                    window.location.href = '/module/manage?module_id=' + moduleId;
                                                }
                                            }
                                        }
                                    });
                                } else {
                                    bootbox.alert('Error: ' + r.error);
                                }
                            },
                            complete: function() {
                                closeModal('delete_fade', 'delete_modal');
                            },
                            async: true
                        }
                    )
                }
            },
            cancel: {
                label: 'No',
                className: 'btn-default',
                callback: function() {
                    return;
                }
            }
        }
    })
})

$('.btn_change_permission').bind('click', function() {
    var moduleId = getURLParameter('module_id');
    var isPublic = $(this).attr('is_public');
    $.ajax({
        url: '/module/permission',
        type: 'POST',
        data: {
            'module_id': moduleId,
            'is_public': isPublic
        },
        success: function(r) {
            if (r.status > 0) {
                var isPublicRes = r.is_public;
                if (isPublicRes) {
                    $('#btn_make_public').hide();
                    $('#btn_make_private').show();
                    $('#badge_private').hide();
                    $('#badge_public').show();
                } else {
                    $('#btn_make_private').hide();
                    $('#btn_make_public').show();
                    $('#badge_public').hide();
                    $('#badge_private').show();
                }
            } else {
                bootbox.alert('Error:' + r.error);
            }
        }
    })
})