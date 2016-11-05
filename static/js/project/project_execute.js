/**
 * Created by haibin on 14-5-26.
 */

var executeDiagramInstance;
var isProcessingExecute;
var jobIdNext = 0;
var jobNameIdMap = {};

$(document).ready(function() {
    executeDiagramInstance = getDiagramInstance('execute_diagram_panel');

    $('#schedule_time').datetimepicker();
    setCurrentTimeForScheduleTime();

    $.contextMenu({
        selector: '#executeFlowModal .job',
        callback: function(key, options) {
            var job = $(this);
            if (key == 'disable-self') {
                job.addClass('job_disable');
            } else if (key == 'enable-self') {
                job.removeClass('job_disable');
            } else if (key == 'enable-precedings' || key == 'disable-precedings') {
                var currentId = job.attr("id");
                var precedingJobIds = getPrecedingJobsAndSelf(executeDiagramInstance, job);
                for (var pjIndex in precedingJobIds) {
                    var pjId = precedingJobIds[pjIndex];
                    if (pjId != currentId) {
                        if (key == 'enable-precedings') {
                            $('#' + pjId).removeClass('job_disable');
                        } else if (key == 'disable-precedings') {
                            $('#' + pjId).addClass('job_disable');
                        }
                    }
                }
            } else if (key == 'enable-followings' || key == 'disable-followings') {
                var currentId = job.attr("id");
                var followingJobIds = getFollowingJobsAndSelf(executeDiagramInstance, job);
                for (var fjIndex in followingJobIds) {
                    var fjId = followingJobIds[fjIndex];
                    if (fjId != currentId) {
                        if (key == 'enable-followings') {
                            $('#' + fjId).removeClass('job_disable');
                        } else if (key == 'disable-followings') {
                            $('#' + fjId).addClass('job_disable');
                        }
                    }
                }
            } else if (key == 'ignore-failed-self') {
                var currentId = job.attr("id");
                var job = $('#' + currentId);
                if (job.hasClass('job_ignore_failed')) {
                    job.removeClass('job_ignore_failed');
                } else {
                    $('#' + currentId).addClass('job_ignore_failed');
                }
            }

            // TODO: add callback logic to other items of context-menu
        },
        items: {
            /* TODO
            'detail': {name: 'Open Job In New Window'},
            'sep1': '-----------------',
            */
            'enable': {
                'name': 'Enable',
                'items': {
                    'enable-self': {name: 'Self'},
                    'enable-precedings': {name: 'Precedings'},
                    'enable-followings': {name: 'Followings'}
                    /* TODO,
                    'enable-parents': {name: 'Parents'},
                    'enable-ancestors': {name: 'Ancestors'},
                    'enable-children': {name: 'children'},
                    'enable-all': {name: 'Enable All'}
                    */
                }
            },
            'disable': {
                'name': 'Disable',
                'items': {
                    'disable-self': {name: 'Self'},
                    'disable-precedings': {name: 'Precedings'},
                    'disable-followings': {name: 'Followings'}
                    /* TODO,
                    'disable-parents': {name: 'Parents'},
                    'disable-ancestors': {name: 'Ancestors'},
                    'disable-children': {name: 'children'},
                    'disable-all': {name: 'Disable All'}
                    */
                }
            },
            'ignore-failed': {
                'name': 'Ignore Failed',
                'items': {
                    'ignore-failed-self': {name: 'Self'}
                }
            }
        }
    });
})

function setCurrentTimeForScheduleTime() {
    var myDate = new Date();
    var date = myDate.getFullYear() + '/' + ('0'+ (myDate.getMonth()+1)).slice(-2) + '/' + ('0'+ myDate.getDate()).slice(-2) +
        ' ' + ('0' + myDate.getHours()).slice(-2) + ':' + ('0' + myDate.getMinutes()).slice(-2);
    $("#schedule_time").val(date);
}

function showUpScheduled(projectId, versionId, flowId) {
    $('#executeFlowModal').data('project_id', projectId);
    $('#executeFlowModal').data('version_id', versionId);
    $('#executeFlowModal').data('flow_id', flowId);
    $('#executeFlowModal').data('disabled_jobs', null);
    $('#executeFlowModal').data('is_edit_mode', true);

    removeAll(executeDiagramInstance);
    $('#executeFlowModal').modal();
};

function showUp(projectId, versionId, flowId) {
    showUp(projectId, versionId, flowId, null);
};

function showUp(projectId, versionId, flowId, disabledJobs) {
    showUp(projectId, versionId, flowId, disabledJobs, null);
}

function showUp(projectId, versionId, flowId, disabledJobs, ignoreFailedJobs) {
    $('#executeFlowModal').data('project_id', projectId);
    $('#executeFlowModal').data('version_id', versionId);
    $('#executeFlowModal').data('flow_id', flowId);
    $('#executeFlowModal').data('disabled_jobs', disabledJobs);
    $('#executeFlowModal').data('ignore_failed_jobs', ignoreFailedJobs);
    $('#executeFlowModal').data('is_edit_mode', false);

    removeAll(executeDiagramInstance);
    $('#executeFlowModal').modal();
}

function cleanUp() {
    // set nav
    $(".li_nav").removeClass('active');
    $("#flow_view").addClass('active');

    // set right panel
    $('.li_panel').hide();
    $('.li_panel[li_id=flow_view]').show();
    $('#executeFlowModal .job').remove();

    // set notification tab
    $('#notify_on_first_failure').attr('checked', true);
    $('#notify_on_first_failure').parent().addClass('checked');
    $('#notify_on_last_failure').attr('checked', true);
    $('#notify_on_last_failure').parent().addClass('checked');
    $('#success_emails').text("");
    $('#failure_emails').text("");

    // set failure options
    $('#failure_action').val("finish_current_running");
    $('#failure_action').select2();

    // set concurrent
    $('#concurrent_option_skip').attr('checked', true);
    $('#concurrent_option_skip').parent().addClass('checked');
    $('#concurrent_option_ignore').attr('checked', false);
    $('#concurrent_option_ignore').parent().removeClass('checked');
    $('#concurrent_option_pipeline').attr('checked', false);
    $('#concurrent_option_pipeline').parent().removeClass('checked');
    $('#pipeline_level').val(1);
    $('#pipeline_level').select2();

    // set hadoop options
    $("#kerberos_keys").val("");
    $("#kerberos_keys").select2();
    $("#queue_name").val("");

    // set advanced options
    $("#colliexe_nodes").val(-1);
    $("#colliexe_nodes").select2();

    // set schedule flow options
    setCurrentTimeForScheduleTime();
    $('#schedule_recurring').attr("checked", true);
    $('#schedule_recurring').parent().addClass("checked");
    $('#schedule_period_number').val(12);
    $('#schedule_period_unit').val("d");
    $('#schedule_period_unit').select2();
}

$('#executeFlowModal').on('hidden.bs.modal', function () {
    removeAll(executeDiagramInstance);
    $('#hadoop_options').hide();
})

$('#executeFlowModal').bind('shown', function() {
    var projectId = $(this).data('project_id');
    var versionId = $(this).data('version_id');
    var flowId = $(this).data('flow_id');
    var disabledJobs = $(this).data('disabled_jobs');
    var ignoreFailedJobs = $(this).data('ignore_failed_jobs');
    var isEditMode = $(this).data('is_edit_mode');
    var scheduledNodeId = -1;

    cleanUp();

    jQuery.ajax({
        url: '/project/flow/options_execute',
        data: {
            'project_id': projectId,
            'version_id': versionId,
            'job_id': flowId,
            'is_edit_mode': isEditMode
        },
        success: function(r) {
            if (r.status > 0) {
                /*************************** Flow View ****************************/
                var jobs = r.jobs;
                for (var jobIndex in jobs) {
                    var job = jobs[jobIndex];
                    var jobName = job['name'];
                    var jobId = 'execute_' + jobIdNext++;
                    job['job_id'] = jobId;
                    jobNameIdMap[jobName] = jobId;
                    var jobDiv = addJob(executeDiagramInstance, job);
                    jobDiv.data('job_name', jobName);
                }

                var connections = r.connections;
                for (var connectionIndex in connections) {
                    var connection = connections[connectionIndex];
                    var sourceName = connection['source_id'];
                    var targetName = connection['target_id'];

                    var sourceId = jobNameIdMap[sourceName];
                    var targetId = jobNameIdMap[targetName];

                    addConnection(executeDiagramInstance, $('#' + sourceId), $('#' + targetId));
                }

                setEditable(executeDiagramInstance, false);

                if (disabledJobs != null) {
                    for (var i in disabledJobs) {
                        jobName = disabledJobs[i];
                        $('#executeFlowModal .job').each(function(_, job) {
                            if ($(job).data('job_name') == jobName) {
                                $(job).addClass('job_disable');
                            }
                        })
                    }
                }

                if (ignoreFailedJobs != null) {
                    for (var i in ignoreFailedJobs) {
                        jobName = ignoreFailedJobs[i];
                        $('#executeFlowModal .job').each(function(_, job) {
                            if ($(job).data('job_name') == jobName) {
                                $(job).addClass('job_ignore_failed');
                            }
                        })
                    }
                }
                /*******************************************************************************/

                /***************************** Hadoop Options *********************************/
                var kkeys = r.kkeys;
                $('#kerberos_keys option').filter(function() {return $(this).val() != 'None';}).remove();
                for (var keyIndex in kkeys) {
                    var key = kkeys[keyIndex];
                    var keyName = key['name'];
                    var nodeOption = new Option();
                    nodeOption.value = keyName;
                    nodeOption.text = keyName;
                    $('#kerberos_keys').append(nodeOption);
                    if (keyIndex == 0) {
                        $('#kerberos_keys').val(keyName);
                        $('#kerberos_keys').select2();
                    }
                }

                if (r.mandatory_hadoop) {
                    $('#hadoop_options').show();
                    if (r.has_yarn_job) {
                        $('#yarn_cluster_option').show();
                        $('#yarn_cluster option').remove();
                        for (var clusterIndex in r.yarn_clusters) {
                            var clusterName = r.yarn_clusters[clusterIndex];
                            var clusterOption = new Option();
                            clusterOption.value = clusterName;
                            clusterOption.text = clusterName;
                            $('#yarn_cluster').append(clusterOption);
                            if (clusterIndex == 0) {
                                $('#yarn_cluster').val(clusterName);
                                $('#yarn_cluster').select2();
                            }
                        }
                    } else {
                        $('#yarn_cluster_option').hide();
                    }
                } else {
                    $('#hadoop_options').hide();
                }

                if( r.mandatory_hadoop && kkeys.length <= 0) {
                    bootbox.dialog({
                        'title': 'Alert',
                        'message': 'Please upload kerberos file when submit yarn or spark jobs',
                        'buttons': {
                            'success': {
                                'class': 'btn-default',
                                'label': 'Fix it',
                                callback: function() {
                                    window.open('/profile/kerberos');
                                }
                            }
                        }
                    })
                }
                $('#queue_option').show();
                /*******************************************************************************/

                /******************************* Notification **********************************/
                var username = r.username;
                var defaultEmail = username + '@xiaomi.com'
                $('#failure_emails').text(defaultEmail)
                $('#success_emails').text(defaultEmail)
                /*******************************************************************************/

                /****************************** Fit Scheduled Info *****************************/
                if (isEditMode && r["scheduled_info"] != null) {
                    var scheduledInfo = r["scheduled_info"];

                    // set flow view tab
                    var flowData = scheduledInfo["flow_data"];
                    var flowJobs = flowData["jobs"];
                    for (var jobId in flowJobs) {
                        var jobInfo = flowJobs[jobId]
                        $('#executeFlowModal .job').each(function(_, job) {
                            if ($(job).data('job_name') == jobInfo["jobId"] && jobInfo["jobStatus"] == "DISABLED") {
                                $(job).addClass('job_disable');
                            }
                            if ($(job).data('job_name') == jobInfo["jobId"] && "ignoreFailed" in jobInfo && jobInfo["ignoreFailed"]) {
                                $(job).addClass('job_ignore_failed');
                            }
                        })
                    }

                    // set notification tab
                    console.info(flowData);
                    var executionOptions = flowData["executionOptions"];
                    var notifyOnFirstFailure = executionOptions["notifyOnFirstFailure"];
                    var notifyOnLastFailure = executionOptions["notifyOnLastFailure"];
                    $('#notify_on_first_failure').attr('checked', notifyOnFirstFailure);
                    if (!notifyOnFirstFailure) {
                        $('#notify_on_first_failure').parent().removeClass('checked');
                    }
                    $('#notify_on_last_failure').attr('checked', notifyOnLastFailure);
                    if (!notifyOnLastFailure) {
                        $('#notify_on_last_failure').parent().removeClass('checked');
                    }
                    var successEmails = executionOptions["successEmails"];
                    $('#success_emails').text(successEmails.join());
                    var failureEmails = executionOptions["failureEmails"];
                    $('#failure_emails').text(failureEmails.join());

                    // set failure options
                    $('#failure_action').val(executionOptions["failureAction"].toLowerCase());
                    $('#failure_action').select2();

                    // set concurrent
                    var concurrentOption = executionOptions['concurrentOption'];
                    $(".li_panel[li_id=concurrent] .radio input").each(
                        function() {
                            $(this).attr('checked', false);
                            $(this).parent().removeClass('checked');
                        }
                    );
                    if (concurrentOption == 'SKIP') {
                        $('#concurrent_option_skip').attr('checked', true);
                        $('#concurrent_option_skip').parent().addClass('checked');
                    } else if (concurrentOption == 'IGNORE') {
                        $('#concurrent_option_ignore').attr('checked', true);
                        $('#concurrent_option_ignore').parent().addClass('checked');
                    } else if (concurrentOption == 'PIPELINE') {
                        $('#concurrent_option_pipeline').attr('checked', true);
                        $('#concurrent_option_pipeline').parent().addClass('checked');
                        var pipelineLevel = executionOptions["pipelineLevel"];
                        $('#pipeline_level').val(pipelineLevel);
                        $('#pipeline_level').select2();
                    }

                    // set hadoop options
                    if ("flowParameters" in executionOptions && "kerberosKey" in executionOptions["flowParameters"]) {
                        var kerberosKey = executionOptions["flowParameters"]["kerberosKey"];
                        var queueName = executionOptions["flowParameters"]["queueName"];
                        $("#kerberos_keys").val(kerberosKey);
                        $("#kerberos_keys").select2();
                        $("#queue_name").val(queueName);
                    }

                    // set advanced options & option will be set when get colliexe_nodes
                    scheduledNodeId = flowData["nodeId"];

                    // set schedule flow options
                    var firstCheckTime = scheduledInfo["first_check_time"];
                    var firstCheckDate = new Date(firstCheckTime);
                    firstCheckDate = new Date(firstCheckDate.getTime() + firstCheckDate.getTimezoneOffset() * 60 * 1000);
                    var firstCheckDateStr = firstCheckDate.getFullYear() + '/' + ('0'+ (firstCheckDate.getMonth()+1)).slice(-2)
                        + '/' + ('0'+ firstCheckDate.getDate()).slice(-2) + ' ' + ('0' + firstCheckDate.getHours()).slice(-2)
                        + ':' + ('0' + firstCheckDate.getMinutes()).slice(-2);
                    $("#schedule_time").val(firstCheckDateStr);
                    var period = scheduledInfo["period"];
                    var periodNumber = period.substring(0, period.length - 1);
                    var periodUnit = period.substring(period.length - 1, period.length);
                    $('#schedule_recurring').attr("checked", true);
                    $('#schedule_recurring').parent().addClass("checked");
                    $('#schedule_period_number').val(periodNumber);
                    $('#schedule_period_unit').val(periodUnit);
                    $('#schedule_period_unit').select2();
                }
                /*******************************************************************************/
            } else {
                bootbox.alert("Error: " + r.error);
                return;
            }
        },
        async: false
    });

    jQuery.ajax({
        url: '/project/flow/colliexe_nodes',
        data: {
        },
        success: function(r) {
            if (r.status > 0) {
                var colliexeNodes = r.colliexe_nodes;
                $('#colliexe_nodes option').filter(function() {return $(this).val() >= 0;}).remove();
                for (var nodeId in colliexeNodes) {
                    var node = colliexeNodes[nodeId];
                    var nodeId = node['id'];
                    var nodeHost = node['host'];
                    var nodeOption = new Option();
                    nodeOption.value = nodeId;
                    nodeOption.text = nodeHost;
                    $('#colliexe_nodes').append(nodeOption);
                }

                if (isEditMode) {
                    $("#colliexe_nodes").val(scheduledNodeId);
                    $("#colliexe_nodes").select2();
                }
            } else {
                bootbox.alert("Error: " + r.error);
                return;
            }
        },
        async: false
    });
});

$('#flow_schedule').bind('click', function() {
    $('#scheduleModal').modal();
});

$('.btn_execute').bind('click', function() {
    console.info('click execute button ...');
    openModal('run_fade', 'run_modal');

    if (!validateHadoopOptionsIfMandatory()) {
        closeModal('run_fade', 'run_modal');
        bootbox.alert('Error: please fill in mandatory hadoop options');
        return false;
    } else {
        var projectId = $('#executeFlowModal').data('project_id');
        var versionId = $('#executeFlowModal').data('version_id');
        var flowJobs = exportFlowJobs();
        $.ajax({
            url: '/project/flow/execute',
            type: 'POST',
            data: {
                'project_id': projectId,
                'version_id': versionId,
                'flow_jobs': flowJobs,
                'options': getOptions()
            },
            success: function(r) {
                console.info('get result from execute flow' + r);
                closeModal('run_fade', 'run_modal');

                if (r.status <= 0) {
                    bootbox.alert('Error: ' + r.message);
                } else {
                    bootbox.dialog({
                        message: 'Submitted...',
                        buttons: {
                            success: {
                                label: 'OK',
                                callback: function() {
                                    window.location.replace("/project/execution/index?execution_id=" + r.execution_id);
                                }
                            }
                        }
                    });
                }
            },
            async: true
        });
    }
});

$('#btn_run_schedule').bind('click', function() {
    openModal('run_fade', 'run_modal');

    if (!validateHadoopOptionsIfMandatory()) {
        closeModal('run_fade', 'run_modal');
        bootbox.alert('Error: please fill in mandatory hadoop options');
        return;
    }

    var projectId = $('#executeFlowModal').data('project_id');
    var versionId = $('#executeFlowModal').data('version_id');
    var isEditMode = $('#executeFlowModal').data('is_edit_mode');
    var flowJobs = exportFlowJobs();

    $.post(
        '/project/flow/schedule',
        {
            'project_id': projectId,
            'version_id': versionId,
            'flow_jobs': flowJobs,
            'is_edit_mode': isEditMode,
            'options': getOptions(),
            'schedule_options': JSON.stringify({
                'datetime': $('#schedule_time').val(),
                'datetime_zone': $('#schedule_datetime_zone').val(),
                'recurring': $('#schedule_recurring').is(':checked'),
                'period_number': $('#schedule_period_number').val(),
                'period_unit': $('#schedule_period_unit').val()
            })
        },
        function(r) {
            closeModal('run_fade', 'run_modal');

            if (r.status > 0) {
                document.location.href = '/project/scheduled/index';
            } else {
                bootbox.alert("Error: " + r.error);
            }
        }
    );
});

$('.li_nav').bind('click', function() {
    // inactive current active li & hide active panel
    var liNavActive = $('.li_nav.active');
    var liNavActiveId = liNavActive.attr('id');
    var liNavActivePanel = $('.li_panel[li_id=\'' + liNavActiveId + '\']');
    liNavActivePanel.hide();
    liNavActive.removeClass('active');

    // active selected li & panel
    var liNav = $(this);
    liNav.addClass('active');
    var liNavId = liNav.attr('id');
    var liNavPanel = $('.li_panel[li_id=\'' + liNavId + '\']');
    liNavPanel.show();
})

$('#advanced_display').bind('click', function() {
    $('#option_running_node').show();
    $(this).hide();
    $('#advanced_hide').show();
})

$('#advanced_hide').bind('click', function() {
    $('#option_running_node').hide();
    $(this).hide();
    $('#advanced_display').show();
})

function validateHadoopOptionsIfMandatory() {
    if ($('#hadoop_options').is(':visible')) {
        var kerberosKey = $('#kerberos_keys').val();
        var queueName = $('#queue_name').val();
        if (kerberosKey == null || queueName == "") {
            return false;
        }
    }
    return true;
}

// return option with json format
function getOptions() {
    var options = {
        notify_on_first_failure: $('#notify_on_first_failure').is(':checked'),
        notify_on_last_failure: $('#notify_on_last_failure').is(':checked'),
        failure_emails_override: $('#failure_emails_override').is(':checked'),
        failure_emails : $('#failure_emails').val(),
        success_emails_override: $('#success_emails_override').is(':checked'),
        success_emails: $('#success_emails').val(),
        failure_action: $('#failure_action').val(),
        concurrent_option_skip: $('#concurrent_option_skip').is(':checked'),
        concurrent_option_ignore: $('#concurrent_option_ignore').is(':checked'),
        concurrent_option_pipeline: $('#concurrent_option_pipeline').is(':checked'),
        pipeline_level: $('#pipeline_level').val(),
        colliexe_node_id: $('#colliexe_nodes').val(),
        kerberos_key: $('#kerberos_keys').val() != null ? $('#kerberos_keys').val() : "None",
        queue_name: $('#queue_name').val(),
        yarn_cluster: $('#yarn_cluster').val()
    }
    return JSON.stringify(options);
}

function exportFlowJobs() {
    var flowJobs = {};
    $('#' + executeDiagramInstance.Defaults.Container + " .job").each(function(){
        var job = $(this);
        var jobName = job.data('job_name');
        var status = 'READY';
        if (job.hasClass('job_disable')) {
            status = 'DISABLED';
        }
        flowJobs[jobName] = {'status': status};
        /** set ignore failed **/
        if (job.hasClass('job_ignore_failed')) {
            flowJobs[jobName]['ignore_failed'] = true;
        } else {
            flowJobs[jobName]['ignore_failed'] = false;
        }
    });
    return JSON.stringify(flowJobs);
};