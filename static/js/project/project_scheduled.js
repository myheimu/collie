/**
 * Created by haibin on 14-3-6.
 */

$(document).ready(function(){
    $('#sidebar li').removeClass('active');
    $('#bar-scheduled').addClass('active');
})

$('.schedule_delete').bind('click', function(r) {
    var scheduledId = $(this).attr('scheduled_id')
    $.post(
        '/project/scheduled/delete',
        {
            'scheduled_id': scheduledId
        },
        function(r) {
            if (r.status) {
                document.location.href = '/project/scheduled/index';
            } else {
                alert('remove failed');
            }
        }
    )
})