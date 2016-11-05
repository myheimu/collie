/**
 * Created by haibin on 14-5-21.
 */

function getDiagramInstance(diagramPanelId) {
    var diagramInstance = null;

    jsPlumb.ready(function(){
        // setup some defaults for jsPlumb.
        diagramInstance = jsPlumb.getInstance({
            Endpoint : ["Dot", {radius:2}],
            HoverPaintStyle : {strokeStyle:"#1e8151", lineWidth:2 },
            ConnectionOverlays : [
                [ "Arrow", {
                    location:1,
                    id:"arrow",
                    length:14,
                    foldback:0.8
                } ],
                [ "Label", { label:"next", id:"label", cssClass:"aLabel" }]
            ],
            Container: diagramPanelId
        });
    });

    return diagramInstance;
}

function setEditable(diagramInstance, isEditable) {
    if (isEditable) {
        diagramInstance.setDraggable($('.job'), true);
        diagramInstance.setSourceEnabled($('.job'), true);
        diagramInstance.bind("dblclick", function(c) {
           diagramInstance.detach(c);
        });
    } else {
        diagramInstance.setDraggable($('.job'), false);
        diagramInstance.setSourceEnabled($('.job'), false);
        diagramInstance.unbind('dblclick');
    }
}

function addJob(diagramInstance, job) {
    var container = diagramInstance.Defaults.Container;

    var jobId = job['job_id'];
    var jobName = job['name'];
    var moduleId = job['module_id'];
    var moduleVersion = job['module_version'];
    var left = job['left'];
    var top = job['top'];

    // get module name
    var moduleName = '';
    jQuery.ajax({
        url: '/module/detail',
        data: {
            'module_id': moduleId
        },
        success: function(r) {
            if (r.status > 0) {
                moduleName = r.name;
            } else {
                bootbox.alert('Error: get module detail failed');
                return;
            }
        },
        async: false
    });

    var job = $("<div class=\"job\"><div class=\"dependency\"></div></div>");
    job.append(jobName + '<br/>' + moduleName + '(' + moduleVersion +')')
    job.attr('id', jobId);
    job.css({top: top, left: left});
    job.appendTo($('#' + container));

    diagramInstance.draggable(job);
    
    diagramInstance.bind("connection", function(info) {
        // info.connection.getOverlay("label").setLabel(info.connection.id);
    });

    diagramInstance.doWhileSuspended(function() {
        diagramInstance.makeSource(job, {
            filter:".dependency",				// only supported by jquery
            anchor:"Continuous",
            connector:[ "StateMachine", { curviness:20 } ],
            connectorStyle:{ strokeStyle:"#5c96bc", lineWidth:2, outlineColor:"transparent", outlineWidth:4 },
            maxConnections:10,
            onMaxConnections:function(info, e) {
                bootbox.alert("Maximum connections (" + info.maxConnections + ") reached");
            }
        });

        diagramInstance.makeTarget(job, {
            dropOptions:{ hoverClass:"dragHover" },
            anchor:"Continuous"
        });
    });

    return job;
}

function setJobStatus(job, status) {
    status = status.toLowerCase();
    if (status == 'ready') {
        ;
    } else if (status == 'running') {
        job.addClass('job_running');
    } else if (status == 'succeeded') {
        job.addClass('job_succeeded');
    } else if (status == 'failed') {
        job.addClass('job_failed');
    } else if (status == 'disabled') {
        job.addClass('job_disabled');
    }
}

function setJobIgnoreFailed(job) {
    job.addClass('job_ignore_failed');
}

function addConnection(diagramInstance, source, target) {
    diagramInstance.connect({
        source: source,
        target: target,
        anchors: ['Right', 'Left'],
        endpoint: 'Rectangle',
        endpointStyle:{ fillStyle: 'yellow' }
    });
}

function removeAll(diagramInstance) {
    var container = diagramInstance.Defaults.Container;
    diagramInstance.detachEveryConnection();
    $('#' + container + ' .job').remove();
}

function getPrecedingJobsAndSelf(diagramInstance, job) {
    var previewJobsMap = {};
    var connections = diagramInstance.getAllConnections();
    for (var conIndex in connections) {
        var con = connections[conIndex];
        var sourceId = con.sourceId;
        var targetId = con.targetId;
        if (!(targetId in previewJobsMap)) {
            previewJobsMap[targetId] = [];
        }
        previewJobsMap[targetId].push(sourceId);
    }

    var result = [];
    var queue = [];
    var jobName = job.attr("id");
    queue.push(jobName);
    while (queue.length > 0) {
        var jn = queue.shift();
        result.push(jn);
        if (jn in previewJobsMap) {
            var previewJobs = previewJobsMap[jn];
            for (var pjIndex in previewJobs) {
                var pj = previewJobs[pjIndex];
                queue.push(pj);
            }
        }
    }

    return result;
}

function getFollowingJobsAndSelf(diagramInstance, job) {
    var followingJobsMap = {}
    var connections = diagramInstance.getAllConnections()
    for (var conIndex in connections) {
        var con = connections[conIndex];
        var sourceId = con.sourceId;
        var targetId = con.targetId;
        if (!(sourceId in followingJobsMap)) {
            followingJobsMap[sourceId] = [];
        }
        followingJobsMap[sourceId].push(targetId);
    }

    var result = [];
    var queue = [];
    var jobName = job.attr("id");
    queue.push(jobName);
    while (queue.length > 0) {
        var jn = queue.shift();
        result.push(jn);
        if (jn in followingJobsMap) {
            var followingJobs = followingJobsMap[jn];
            for (var fjIndex in followingJobs) {
                var fj = followingJobs[fjIndex];
                queue.push(fj);
            }
        }
    }

    return result;
}