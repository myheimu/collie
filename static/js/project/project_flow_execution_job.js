/**
 * Created by haibin on 14-5-26.
 */

$(document).ready(function() {
    var logPanel = $('.log_panel');
    logPanel.scrollTop(logPanel[0].scrollHeight);
})

$('#log_refresh').bind('click', function() {
    $.get(
        '/project/execution/job/log',
        {
            'execution_id': getURLParameter('execution_id'),
            'job_id': getURLParameter('job_id')
        },
        function(r) {
            if (r.status > 0) {
                var logPanel = $('.log_panel');
                logPanel.attr('log_offset', r.log_offset);
                logPanel.val(r.log_data);
                logPanel.scrollTop(logPanel[0].scrollHeight);
            } else {
                bootbox.alert(r.error);
            }
        }
    )
})
