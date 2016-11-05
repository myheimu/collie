/**
 * Created by haibin on 14-5-8.
 */

var diagramInstance;
var jobIdNext = 0;
var jobNameIdMap = {};
var disabledJobs = new Array();
var ignoreFailedJobs = new Array();

$(document).ready(function() {
    diagramInstance = getDiagramInstance('flow_diagram_panel');
    if (diagramInstance == null) {
        bootbox.alert('Error: get diagram instance failed');
    }

    $.get(
        '/project/execution/diagram',
        {
            'execution_id': getURLParameter('execution_id')
        },
        function(r) {
            if (r.status > 0) {
                var jobs = r.jobs;
                var executionStatus = r.execution_status;
                if (executionStatus == 'RUNNING') {
                    $('#btn_execution_pause').show();
                    $('#btn_execution_cancel').show();
                } else if (executionStatus == 'PAUSED') {
                    $('#btn_execution_resume').show();
                } else if (executionStatus == 'FAILED' || executionStatus == 'SUCCEEDED') {
                    $('#btn_execution_rerun').show();
                } else if (executionStatus == 'FAILED_FINISHING') {
                    $('#btn_execution_cancel').show();
                }

                var connections = r.connections;
                for (var jobIndex in jobs) {
                    var jobJson = jobs[jobIndex];
                    var jobName = jobJson['name'];
                    var jobId = "job_" + jobIdNext++;
                    jobJson['job_id'] = jobId;
                    jobNameIdMap[jobName] = jobId;
                    var job = addJob(diagramInstance, jobJson);
                    /** set job status **/
                    setJobStatus(job, jobJson['status']);
                    if (jobJson['status'] == 'SUCCEEDED' || jobJson['status'] == 'DISABLED') {
                        disabledJobs.push(jobName);
                    }
                    if ('ignore_failed' in jobJson && jobJson['ignore_failed']) {
                        ignoreFailedJobs.push(jobName);
                    }
                    /** set ignore failed **/
                    var ignoreFailed = jobJson['ignore_failed'];
                    if (ignoreFailed) {
                        setJobIgnoreFailed(job);
                    }
                }
                for (var connectionIndex in connections) {
                    var connection = connections[connectionIndex];
                    var sourceName = connection['source_id'];
                    var targetName = connection['target_id'];
                    var source = $('#' + jobNameIdMap[sourceName]);
                    var target = $('#' + jobNameIdMap[targetName]);
                    addConnection(diagramInstance, source, target)
                }
                setEditable(diagramInstance, false);
            } else {
                bootbox.alert(r.error);
            }
        }
    )
})

$('#btn_execution_rerun').bind('click', function(){
    var projectId = $('.main_panel').attr('project_id');
    var projectVersion = $('.main_panel').attr('project_version');
    var flowId = $('.main_panel').attr('flow_id');

    showUp(projectId, projectVersion, flowId, disabledJobs, ignoreFailedJobs);
})

$('#btn_execution_pause').bind('click', function(){
    var executionId = $('.main_panel').attr('execution_id');
    $.post(
        '/project/execution/pause',
        {
            'execution_id': executionId
        },
        function(r) {
            if (r.status > 0) {
                bootbox.dialog({
                    message: 'pause successfully',
                    buttons: {
                        success: {
                            label: 'Done',
                            callback: function() {
                                $('#btn_execution_pause').hide();
                                $('#btn_execution_cancel').hide();
                                $('#btn_execution_resume').show();
                                location.reload();
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

$('#btn_execution_cancel').bind('click', function(){
    var executionId = $('.main_panel').attr('execution_id');
    $.post(
        '/project/execution/cancel',
        {
            'execution_id': executionId
        },
        function(r) {
            if (r.status > 0) {
                bootbox.dialog({
                    message: 'cancel successfully',
                    buttons: {
                        success: {
                            label: 'Done',
                            callback: function() {
                                $('#btn_execution_pause').hide();
                                $('#btn_execution_cancel').hide();
                                $('#btn_execution_resume').hide();
                                location.reload();
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

$('#btn_execution_resume').bind('click', function(){
    var executionId = $('.main_panel').attr('execution_id');
    $.post(
        '/project/execution/resume',
        {
            'execution_id': executionId
        },
        function(r) {
            if (r.status > 0) {
                bootbox.dialog({
                    message: 'resume successfully',
                    buttons: {
                        success: {
                            label: 'Done',
                            callback: function() {
                                $('#btn_execution_pause').show();
                                $('#btn_execution_cancel').show();
                                $('#btn_execution_resume').hide();
                                location.reload();
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

$('#log_refresh').bind('click', function() {
    $.get(
        '/project/execution/log',
        {
            'execution_id': getURLParameter('execution_id')
        },
        function(r) {
            if (r.status > 0) {
                var logPanel = $('.log_panel');
                logPanel.attr('log_offset', r.log_offset);
                logPanel.val(r.log_data);
            } else {
                bootbox.alert(r.error);
            }
        }
    )
})