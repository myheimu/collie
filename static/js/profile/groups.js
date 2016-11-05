/**
 * Created by haibin on 14-7-1.
 */

$('.modal').bind('hidden.bs.modal', function() {
    $('.verify_result').text('');
    $('.input_group_name').val('');
})

$('.verify_group_name').bind('click', function() {
    var groupName = $('#group_name_join').val();
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

$('#btn_create_group').bind('click', function() {
    var groupName = $('#group_name_create').val();
    $.post(
        '/profile/group/create',
        {
            'group_name': groupName
        },
        function(r) {
            if (r.status > 0) {
                document.location.href = '/profile/groups';
            } else {
                bootbox.alert('Error: ' + r.error);
            }
        }
    )
})

$('#btn_join_group').bind('click', function() {
    var groupName = $('#group_name_join').val();
    $.post(
        '/profile/group/join',
        {
            'group_name': groupName
        },
        function(r) {
            if (r.status > 0) {
                bootbox.dialog({
                    'message': 'apply to join group successfully',
                    'buttons': {
                        'success': {
                            label: 'OK',
                            callback: function() {
                                document.location.href = '/profile/groups';
                            }
                        }
                    }
                });
            } else {
                bootbox.alert(r.error);
            }
        }
    )
})

$('.btn_approve').bind('click', function() {
    var userName = $(this).parent().attr('user_name');
    var groupName = $(this).parent().attr('group_name');
    $.post(
        '/profile/group/approve',
        {
            'group_name': groupName,
            'applicant_name': userName
        },
        function(r) {
            if (r.status > 0) {
                document.location.href = '/profile/groups';
            } else {
                bootbox.alert('Error: ' + r.error);
            }
        }
    )
})

$('.btn_deny').bind('click', function() {
    var userName = $(this).parent().attr('user_name');
    var groupName = $(this).parent().attr('group_name');
    $.post(
        '/profile/group/deny',
        {
            'group_name': groupName,
            'applicant_name': userName
        },
        function(r) {
            if (r.status > 0) {
                document.location.href = '/profile/groups';
            } else {
                bootbox.alert('Error: ' + r.error);
            }
        }
    )
})

$('.btn_leave').bind('click', function() {
    var groupName = $(this).parent().attr('group_name');
    $.post(
        '/profile/group/leave',
        {
            'group_name': groupName
        },
        function(r) {
            if (r.status > 0) {
                document.location.href = '/profile/groups';
            } else {
                bootbox.alert('Error: ' + r.error);
            }
        }
    )
})