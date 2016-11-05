/**
 * Created by haibin on 14-3-11.
 */

var mode;
var instance;
var jobIdNext = 0;
var jobNameIdMap = {}
var currentProjectId;
var currentProjectVersion;

jsPlumb.ready(function(){
    // setup some defaults for jsPlumb.
    instance = jsPlumb.getInstance({
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
        Container:"project-panel"
    });

    instance.bind("dblclick", function(c) {
        instance.detach(c);
    });

    instance.bind("connection", function(c) {
        // check has circle in current diagram
        if (hasCircle(c)) {
            instance.detach(c);
            bootbox.alert('Error: found circle when add flow sequence');
        } else if (hasDuplicate(c)) {
            instance.detach(c);
            bootbox.alert('Error: found duplicate sequence when add flow sequence');
        } else {
            // c.connection.getOverlay("label").setLabel(c.connection.id);
        }
    });
});

$(document).ready(function() {
    currentProjectId = getURLParameter('project_id');
    currentProjectVersion = getURLParameter('project_version');

    // get page mode
    mode = getURLParameter('mode');
    if (mode == '') {
        mode = 'view';
    }

    initPage();
    resetPage();

    $.contextMenu({
        selector: '#project-panel .job',
        callback: function(key, options) {
            var job = $(this);
            if (key == 'detail') {
                // TODO
            } else if (key == 'update') {
                openEditJobModal('update', job.data('id'), job.data('module_id'), job.data('module_version'));
            } else if (key == 'delete') {
                instance.detachAllConnections(job);
                job.remove();
            }

            // TODO: add callback logic to other items of context-menu
        },
        items: {
            'detail': {name: 'Open Job In New Window'},
            'sep1': '-----------------',
            'update': {
                name: 'Update',
                disabled: function(key, opt) { return mode == 'view';}
            },
            'delete': {
                name: 'Delete',
                disabled: function(key, opt) { return mode == 'view';}
            }
        }
    });

    window.onbeforeunload=goodbye;
});

$('#edit_project').bind('click', function() {
    mode = 'edit';
    resetPage();
})

function resetPage() {
    if (mode == 'view') {
        /*****************************/
        /********* view mode *********/
        /*****************************/
        resetExecuteFlows();
        $('#execute_project').show();
        $('#save_project').hide();
        $('#edit_project').show();
        $(".add-job").unbind("click");
        instance.setDraggable($('.job'), false);
        instance.setSourceEnabled($('.job'), false);
        instance.unbind('dblclick');
    } else {
        /*****************************/
        /********* edit mode *********/
        /*****************************/
        $('#execute_project').hide();
        $('#edit_project').hide();
        $('#save_project').show();
        $(".add-job").bind("click", function() {
            var moduleId = $(this).attr('module_id');
            openEditJobModal('new', '', moduleId);
        });
        instance.setDraggable($('.job'), true);
        instance.setSourceEnabled($('.job'), true);
        instance.bind("dblclick", function(c) {
           instance.detach(c);
        });
    }
}

$("#save_project").bind("click", function() {
    openModal("saving_fade", "saving_modal");
    console.log(exportDiagramToJson());
    $.ajax({
        type: "POST",
        url: "/project/save",
        data: {
            "project_id": $("#project_id").text(),
            "diagram": exportDiagramToJson()
        },
        success: function(r) {
            if (r.status > 0) {
                currentProjectId = r.project_id;
                currentProjectVersion = r.project_version;
                var message = 'save successfully. ' + r.message;

                bootbox.dialog({
                    message: message,
                    buttons: {
                        success: {
                            label: 'OK',
                            callback: function() {
                                mode = 'view';
                                resetPage();
                            }
                        }
                    }
                });
            } else {
                bootbox.alert("Error: " + r.error);
            }
        },
        complete: function() {
            closeModal("saving_fade", "saving_modal");
        },
        async: true
    });
});

function initPage() {
    var projectId = getURLParameter('project_id');
    var projectVersion = getURLParameter('project_version');

    if (projectVersion == null) {
        return;
    }

    $.ajax({
            url: '/project/detail',
            data: {
                'project_id': projectId,
                'project_version': projectVersion
            },
            success: function(r) {
                if (r.status > 0) {
                    var diagram = r.diagram;
                    var jobs = diagram['jobs'];
                    var connections = diagram['connections'];
                    $.each(jobs, function(_index, job) {
                        var jobDiv = addJobNode(job['name'], job['module_id'], job['module_version'], job['left'], job['top']);
                        jobDiv.data('id', jobDiv.attr('id'));
                        jobDiv.data('name', job['name']);
                        jobDiv.data('description', job['description']);
                        jobDiv.data('module_id', job['module_id']);
                        jobDiv.data('module_version', job['module_version']);
                        jobDiv.data('options', refineOptions(job['options']));
                    });
                    $.each(connections, function(_index, connection) {
                        try {
                            var sourceName = connection['source_id'];
                            var targetName = connection['target_id'];
                            var sourceId = jobNameIdMap[sourceName];
                            var targetId = jobNameIdMap[targetName];
                            instance.connect({
                                source: sourceId,
                                target: targetId,
                                anchors: ['Right', 'Left'],
                                endpoint: 'Rectangle',
                                endpointStyle:{ fillStyle: 'yellow' }
                            });
                        } catch (err) {
                            bootbox.alert('Error: unable to connect jobs');
                        }
                    });
                } else {
                    bootbox.alert('Error: init page failed');
                }
            },
            async: false
        }
    )
}

function refineOptions(oldOptions) {
    // old format: {"spark_args": {"k1":"v1", "k2":"v2"}, "jvm_args":{}}
    // refined(output) format: {"spark_args": [{"key":"k1", "value":"v1"}, {"key":"k2", "value":"v2"}], "jvm_args": []}
    var newOptions = {};
    for (var category in oldOptions) {
        var oldCategoryOptions = oldOptions[category];
        if (oldCategoryOptions.constructor == Array) {
            newOptions[category] = oldCategoryOptions;
        } else {
            var newCategoryOptions = new Array();
            for (var optionKey in oldCategoryOptions) {
                var optionValue = oldCategoryOptions[optionKey];
                var newOption = {"key": optionKey, "value": optionValue};
                newCategoryOptions.push(newOption);
            }
            newOptions[category] = newCategoryOptions;
        }
    }
    return newOptions;
}

function exportDiagramToJson() {
    var resJson = {};

    // convert jobs
    var jobsJson = [];
    $(".job[id!=job_temp]").each(function(){
        var job = $(this);
        jobsJson.push({
            "job_id" : job.data("name"),
            "name": job.data("name"),
            "description": job.data("description"),
            "module_id" : job.data("module_id"),
            "module_version": job.data("module_version"),
            "left" : job.css("left"),
            "top" : job.css("top"),
            "options" : job.data("options")
        });
    });
    resJson["jobs"] = jobsJson;

    // convert connections
    var connectionsJson = [];
    var connections = instance.getAllConnections();
    $.each(connections, function( _index, connection ) {
        var source = connection.source;
        var target = connection.target;
        var sourceDiv = $('#' + source.id);
        var targetDiv = $('#' + target.id);
        connectionsJson.push({
            "source_id" : sourceDiv.data('name'),
            "target_id" : targetDiv.data('name')
        });
    });
    resJson["connections"] = connectionsJson;

    var result = JSON.stringify(resJson);
    console.log(result);
    return result;
};

function addJobNode(jobName, moduleId, moduleVersion, left, top) {
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

    var jobId = "job_" + jobIdNext++;
    jobNameIdMap[jobName] = jobId;
    var job = $('#job_temp').clone(true, true);
    job.append(jobName + '<br/>' + moduleName + '(' + moduleVersion +')')
    job.attr('id', jobId);
    job.css({top: top, left: left});
    job.show();
    $(job).appendTo($('#project-panel'));

    instance.draggable(job);

    instance.doWhileSuspended(function() {
        instance.makeSource(job, {
            filter:".dependency",				// only supported by jquery
            anchor:"Continuous",
            connector:[ "StateMachine", { curviness:20 } ],
            connectorStyle:{ strokeStyle:"#5c96bc", lineWidth:2, outlineColor:"transparent", outlineWidth:4 }
        });

        instance.makeTarget(job, {
            dropOptions:{ hoverClass:"dragHover" },
            anchor:"Continuous",
            maxConnections:10,
            onMaxConnections:function(info, e) {
                alert("Maximum connections (" + info.maxConnections + ") reached");
            }
            });
    });

    return job;
}

$('#version_select').change(function() {
    var versionId = $(this).val();
    $.get(
        '/module/version/detail',
        {
            'version_id': versionId
        },
        function(r) {
            if (r.status > 0) {
                // remove current parameters
                $('.options_div').children('.option_assignment[id!=option_assignment_temp]').remove();

                // parameters
                var options = r.options;
                var type = r.type;
                if (type == 'Shell') {
                    for (var argIndex in options.args) {
                        initJobOption(true, 'args', options.args[argIndex], "", "");
                    }
                } else if (type == 'Jar' || type == 'yarn') {
                    for (var argIndex in options.jvm_args) {
                        initJobOption(true, 'jvm_args', options.jvm_args[argIndex], "", "");
                    }
                    for (var argIndex in options.main_args) {
                        initJobOption(true, 'main_args', options.main_args[argIndex], "", "");
                    }
                } else if (type == 'spark') {
                    for (var argIndex in options.spark_args) {
                        initJobOption(true, 'spark_args', options.spark_args[argIndex], "", "");
                    }
                }
            } else {
                alert('get version detail failed');
            }
        }
    )
})

$('#btn_job_save').bind('click', function() {
    var mode = $('#editJobModal').attr('mode');
    var jobName = $('#editJobModal #job_info #job_name').val();
    var jobDescription = $('#editJobModal #job_info #job_description').val();
    var jobModuleId = $('#editJobModal #job_info #module_name').attr('module_id');
    var jobModuleName = $('#editJobModal #job_info #module_name').text();
    var jobModuleVersion = $('#editJobModal #job_info #version_select').val();
    var jobOptions = {};

    var originalName = $('#editJobModal #job_info').attr('job_original_name');
    var hasSameJobName = false;
    $('.job[id!=job_temp]').each(function(_, job) {
        var existJobName = $(job).data('name');
        var updateWithoutChangeJobName = false;
        if (mode == 'update' && originalName == jobName) {
            updateWithoutChangeJobName = true;
        }

        if (existJobName == jobName && !updateWithoutChangeJobName) {
            hasSameJobName = true;
        }
    })

    if (!jobName.trim()) {
        bootbox.alert('Error: job name is empty.');
        return;
    }

    var regex = /^[0-9a-zA-Z_]+$/
    if (!regex.test(jobName)) {
        bootbox.alert('Error: job name only contain 0-9 a-z A-Z _');
        return;
    }

    if (hasSameJobName) {
        bootbox.alert('Error: exist same name job, please change another name.');
        return;
    }

    $('.option_assignment[id!=option_assignment_temp]').each(function(index, value) {
        var optionName = $(value).children('.option_name').text();
        var optionCategory = $(value).children('.option_category').text();
        var optionValue = $(value).children('input').val();
        if (jobOptions[optionCategory] == null) {
            jobOptions[optionCategory] = new Array()
        }
        jobOptions[optionCategory].push({"key": optionName,"value": optionValue});
    })

    var job;
    if (mode == 'new') {
        job = addJobNode(jobName, jobModuleId, jobModuleVersion, 0, 0);
    } else {
        var jobId = jobNameIdMap[originalName];
        job = $("#" + jobId);
        var dependency = $(job).children('.dependency').clone(true, true);
        job.contents().remove();
        job.append(jobName + '<br/>' + jobModuleName + '(' + jobModuleVersion +')');
        job.append(dependency);
        jobNameIdMap[jobName] = jobId;
    }

    job.data('id', job.attr('id'));
    job.data('name', jobName);
    job.data('description', jobDescription);
    job.data('module_id', jobModuleId);
    job.data('module_version', jobModuleVersion);
    job.data('options', jobOptions);
    $('#editJobModal').modal('toggle');
})

$('.module_link').bind('click', function() {
    var moduleId = $(this).attr('module_id');
    window.open('/module/manage?module_id=' + moduleId);
})

$('.flow').bind('click', function() {
    var flowName = $(this).attr('flow_name');
    showUp(currentProjectId, currentProjectVersion, flowName);
})

function openEditJobModal(mode, jobId, moduleId, versionId) {
    $.get(
        '/module/detail',
        {
            'module_id': moduleId,
            'version_id': versionId
        },
        function(r) {
            if (r.status > 0) {
                if (mode != 'new' && mode != 'update') {
                    alert('unknown mode found');
                    return;
                }
                var isNewMode = (mode == 'new');
                var job = (mode == 'update') ? $("[id='" + jobId + "']") : null;

                $('#editJobModal').attr('mode', mode);
                $('#editJobModal #edit_mode').text(isNewMode ? 'New Job' : 'Update Job');
                $('#editJobModal #job_info').attr('job_id', isNewMode ? '' : jobId);
                $('#editJobModal #job_info').attr('job_original_name', isNewMode ? '' : job.data('name'));
                $('#editJobModal #job_info #job_name').val(isNewMode ? '' : job.data('name'));
                $('#editJobModal #job_info #job_description').val(isNewMode ? '' : job.data('description'));

                // module name
                var moduleName = r.name;
                $('#editJobModal #job_info #module_name').text(moduleName);
                $('#editJobModal #job_info #module_name').attr('module_id', moduleId);

                // remove options
                $('#editJobModal #job_info #version_select').children('option').remove();

                // module version
                for (var versionIndex in r.versions) {
                    var version = r.versions[versionIndex]
                    var versionNo = version.id;
                    var option = new Option(versionNo, versionNo);
                    $(option).attr('version_id', versionNo);
                    $('#editJobModal #job_info #version_select').append(option);
                }
                $('#editJobModal #job_info #version_select').val(isNewMode ? '' : job.data('module_version'));
                $('#editJobModal #job_info #version_select').select2();

                // remove current parameters
                $('.options_div').children('.option_assignment[id!=option_assignment_temp]').remove();

                if (isNewMode) {
                    var options = r.latest_options;
                    var type = r.latest_type;
                    if (type == 'Shell') {
                        for (var argIndex in options.args) {
                            initJobOption(isNewMode, 'args', options.args[argIndex], "", "");
                        }
                    } else if (type == 'Jar' || type == 'yarn') {
                        for (var argIndex in options.jvm_args) {
                            initJobOption(isNewMode, 'jvm_args', options.jvm_args[argIndex], "", "");
                        }
                        for (var argIndex in options.main_args) {
                            initJobOption(isNewMode, 'main_args', options.main_args[argIndex], "", "");
                        }
                    } else if (type == 'spark') {
                        for (var argIndex in options.spark_args) {
                            initJobOption(isNewMode, 'spark_args', options.spark_args[argIndex], "", "");
                        }
                    }
                } else {
                    var job_options = job.data('options')
                    var module_options = r.latest_options;
                    var type = r.latest_type;
                    if (type == 'Shell') {
                        initJobOptions(module_options.args, job_options, 'args', isNewMode);
                    } else if (type == 'Jar' || type == 'yarn') {
                        initJobOptions(module_options.jvm_args, job_options, 'jvm_args', isNewMode);
                        initJobOptions(module_options.main_args, job_options, 'main_args', isNewMode);
                    } else if (type == 'spark') {
                        initJobOptions(module_options.spark_args, job_options, 'spark_args', isNewMode);
                    }
                }

                $('#editJobModal').modal();
            } else {
                bootbox.alert('unable to get info of module ' + moduleId);
            }
        }
    )
}

function initJobOptions(moduleDefOptionArgs, jobOptions, jobOptionCategory, isNewMode) {
    var optionIndexMap = new Map()
    for (var argIndex in moduleDefOptionArgs) {
        var jobOptionName = moduleDefOptionArgs[argIndex]['name'];
        var jobOptionValue = "";

        var optionIndex = optionIndexMap[jobOptionName];
        if (optionIndex == null) optionIndex = 0;

        if (jobOptionCategory in jobOptions) {
            var optionValue = getOptionValueByKeyInArray(jobOptions[jobOptionCategory], jobOptionName, optionIndex);
            if (optionValue != null) {
                jobOptionValue = optionValue;
                optionIndexMap[jobOptionName] = optionIndex + 1;
            }
        }

        initJobOption(isNewMode, jobOptionCategory, '', jobOptionName, jobOptionValue);
    }
}

function getOptionValueByKeyInArray(arr, key, index) {
    var hitIndex = 0;
    for (var i in arr) {
        var item  = arr[i]
        var itemKey = item.key
        var itemValue = item.value
        if (key == itemKey) {
            if (hitIndex == index) {
                return itemValue;
            } else {
                hitIndex += 1;
            }
        }
    }

    return null;
}

function initJobOption(isNewMode, optionCategory, optionNew, optionUpdateName, optionUpdateValue) {
    if (isNewMode) {
        var optionName = optionNew.name;
        var optionValue = optionNew.default;
        if (!optionValue) {
            // get from previous value
            var jobId = $('#editJobModal #job_info').attr('job_id');
            var options = $('#' + jobId).data('options');
            if (options && optionCategory in options) {
                optionValue = options[optionCategory][optionName];
            }
        }
    } else {
        var optionName = optionUpdateName;
        var optionValue = optionUpdateValue;
    }

    var optionAssignment = $('#option_assignment_temp').clone(true, true);
    optionAssignment.attr('id', '');
    optionAssignment.children('.option_name').text(optionName/* + ' (' + optionDescription  + ')'*/);
    optionAssignment.children('.option_category').text(optionCategory);
    optionAssignment.children('input').val(optionValue);
    optionAssignment.show();
    optionAssignment.appendTo($('.options_div'));
}

function hasDuplicate(newConnection) {
    var connections = instance.getAllConnections();
    var count = 0;
    var newSourceId = newConnection['sourceId'];
    var newTargetId = newConnection['targetId'];
    for(var conIndex in connections ) {
        var connection = connections[conIndex];
        var sourceId = connection['sourceId'];
        var targetId = connection['targetId'];
        if (newSourceId == sourceId && newTargetId == targetId) {
            count ++;
        }
    }
    return count > 1;
}

function hasCircle(newConnection) {
    var connections = instance.getAllConnections();

    // construct connection target map
    var targetMap = {}
    for(var conIndex in connections ) {
        var connection = connections[conIndex];
        var sourceId = connection['sourceId'];
        var targetId = connection['targetId'];
        if (!(sourceId in targetMap)) {
            targetMap[sourceId] = []
        }
        targetMap[sourceId].push(targetId);
    }

    // target
    var newSourceId = newConnection['sourceId'];
    var newTargetId = newConnection['targetId'];
    var suspectQueue = [];
    suspectQueue.push(newTargetId);
    while (suspectQueue.length > 0) {
        var suspectId = suspectQueue.shift();
        if(suspectId == newSourceId) {
            return true;
        }
        if (suspectId in targetMap) {
            var targets = targetMap[suspectId];
            for (var targetIndex in targets) {
                suspectQueue.push(targets[targetIndex]);
            }
            delete targetMap[suspectId];
        }
    }

    return false;
}


function resetExecuteFlows() {
    // clear all li under flow div
    $('#flows li[id!=flow_temp]').remove();

    // find all job who has no preceding job
    var connections = instance.getAllConnections();
    var hasPrecedingMap = new Object();
    for (var connectionIndex in connections) {
        var connection = connections[connectionIndex];
        var sourceId = connection.sourceId;
        hasPrecedingMap[sourceId] = true;
    }

    // get all jobs
    var jobs = $('.job[id!=job_temp]');
    var flowRootJobs = new Array();
    jobs.each(function(_, job) {
        var jobId = $(job).attr('id');
        if (!hasPrecedingMap[jobId]) {
            flowRootJobs.push(jobId);
        }
    })

    for (var jobIndex in flowRootJobs) {
        var flowRootJob = flowRootJobs[jobIndex];
        var flow = $('#flow_temp').clone(true, true);
        var jobName = $('#' + flowRootJob).data('name');
        flow.children('a').text('Flow: ' + jobName);
        flow.attr('id', '');
        flow.attr('flow_name', jobName);
        flow.appendTo($('#flows'));
        flow.show();
    }
}

function goodbye(e) {
    if (mode == 'update') {
        e = e || window.event;
        var message = "Without saving project.";
        if (e) {
            e.returnValue = message;
        }
        return message;
    }
}