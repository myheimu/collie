/**
 * Created by haibin on 14-3-4.
 */

var diagramInstance;
var jobIdNext = 0;
var jobNameIdMap = {};

$(document).ready(function() {
    diagramInstance = getDiagramInstance('flow_diagram');
    if (diagramInstance == null) {
        bootbox.alert('Error: get diagram instance failed');
    }

    $.get(
        '/project/flow/diagram',
        {
            'project_id': getURLParameter('project_id'),
            'version_id': getURLParameter('version_id'),
            'flow_id': getURLParameter('job_id')
        },
        function(r) {
            if (r.status > 0) {
                var jobs = r.jobs;
                var connections = r.connections;
                for (var jobIndex in jobs) {
                    var job = jobs[jobIndex];
                    var jobName = job['name'];
                    var jobId = "job_" + jobIdNext++;
                    job['job_id'] = jobId;
                    jobNameIdMap[jobName] = jobId;
                    addJob(diagramInstance, job);
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

$('.btn_edit_scheduled').bind('click', function() {
    var projectId = getURLParameter('project_id');
    var versionId = getURLParameter('version_id');
    var flowId = getURLParameter('job_id');
    showUpScheduled(projectId, versionId, flowId);
})

$('.btn_run').bind('click', function() {
    var projectId = getURLParameter('project_id');
    var versionId = getURLParameter('version_id');
    var flowId = getURLParameter('job_id');
    showUp(projectId, versionId, flowId);
})


