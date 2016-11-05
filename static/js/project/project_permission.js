/**
 * Created by haibin on 14-7-1.
 */

$('#btn_check_group').bind('click', function() {
    var groupName = $('#group_name').val();
    $.get(
        '/profile/group/verify',
        {
            'group_name': groupName
        },
        function(r) {
            if (r.status > 0) {
                $('.verify_result').text(r.result);
            } else {
                bootbox.alert('Error: verify failed');
            }
        }
    )
})

$('#btn_save').bind('click', function() {
    var groupName = $('#group_name').val();
    var role = $('#new_permission_role_select').val();
    savePermission(groupName, role);
})

$('.role_select').change(function() {
    var groupName = $(this).parent().attr('group_name');
    var role = $(this).val();
    savePermission(groupName, role);
})

function savePermission(groupName, role) {
    var projectId = getURLParameter('project_id');
    $.post(
        '/project/permission/grant',
        {
            'project_id': projectId,
            'group_name': groupName,
            'role': role
        },
        function(r) {
            if (r.status > 0) {
                bootbox.dialog({
                    'message': 'save successfully',
                    'buttons': {
                        'success': {
                            'label': 'OK',
                            callback: function() {
                                document.location.href = '/project/permission/index?project_id=' + projectId;
                            }
                        }
                    }
                })
            } else {
                bootbox.alert('Error: ' + r.error);
            }
        }
    )
}

$('.btn_delete').bind('click', function() {
    var groupName = $(this).parent().attr('group_name');
    var projectId = getURLParameter('project_id')
    $.post(
        '/project/permission/revoke',
        {
            'project_id': projectId,
            'group_name': groupName
        },
        function(r) {
            if (r.status > 0) {
                bootbox.dialog({
                    'message': 'delete successfully',
                    'buttons': {
                        'success': {
                            'label': 'OK',
                            callback: function() {
                                document.location.href = '/project/permission/index?project_id=' + projectId;
                            }
                        }
                    }
                })
            } else {
                bootbox.alert('Error: ' + r.error);
            }
        }
    )
})