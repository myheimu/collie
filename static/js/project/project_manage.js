/**
 * Created by haibin on 14-4-10.
 */
var zoomRate = 1.0;
var zoomInterval = 0.1;

$('.activity-list li').bind('mouseenter', function() {
    $(this).find('div .btn-run').css('visibility', '');
});

$('.activity-list li').bind('mouseleave', function() {
    $(this).find('div .btn-run').css('visibility', 'hidden');
});

$('.activity-list li div a').bind('click', function(event) {
    console.info('click me');
})

$('.flow-root div span').bind('click', function(event) {
    event.preventDefault();

    console.log("flow root is clicked");
    var itemClass = $(this).attr('class');

    if (itemClass == "icon-chevron-up") {
        $(this).attr('class', 'icon-chevron-right');
        var jobId = $(this).parent().parent().attr("job_id");
        $(".activity-list li[flow_root='" + jobId + "']").remove();
    } else {
        $(this).attr('class', 'icon-chevron-up');

        $.get(
            "/project/flow/tree",
            {
                'project_id': $("#project_info").attr("project_id"),
                'job_id': $(this).parent().parent().attr("job_id")
            },
            function(r) {
                if (r.status) {
                    var jobId = JSON.parse(r.data).job_id;
                    insertChildren($(".flow-root[job_id='" + jobId + "']"), JSON.parse(r.data), 1);
                } else {
                    alert("get flow detail failed");
                }
            }
        );
    }

});

function insertChildren(root_node, sub_tree, depth) {
    var proceedings = sub_tree.proceedings;
    if (proceedings == null || proceedings.length <= 0) {
        return;
    }

    var flow_root_id = root_node.attr('job_id')
    for (var proceeding_index in proceedings) {
        var proceeding = proceedings[proceeding_index]
        var liElement = $("#leaf-template").clone(true, true);
        liElement.css('margin-left', depth * 20 + "px");
        liElement.attr('job_id', proceeding.job_id);
        liElement.attr('flow_root', flow_root_id);
        liElement.attr('flow_root_job_id', flow_root_id);
        liElement.find('div a').text(proceeding.name);
        liElement.show();
        insertChildren(root_node, proceeding, depth + 1);
        liElement.insertAfter(root_node);
    }
};

$('#view_update_btn').bind('click', function() {
    var projectId = getURLParameter('project_id');
    var projectVersion = getURLParameter('version_id');
    document.location.href = '/project/edit?project_id=' + projectId + "&project_version=" + projectVersion + "&mode=update";
})

$('.btn-run').bind('click', function() {
    var projectId = getURLParameter('project_id');
    var versionId = getURLParameter('version_id');
    var jobId = $(this).parent().parent().attr('flow_root_job_id');
    showUp(projectId, versionId, jobId);
});

/* TODO
$('.flow-panel').bind('mousewheel', function(event) {
    if(event.originalEvent.wheelDelta /120 > 0) {
        if (zoomRate + zoomInterval <= 1.0) {
            zoomRate = zoomRate + zoomInterval;
            // setZoom(zoomRate);
        }
    }
    else {
        if (zoomRate - zoomInterval > 0) {
            zoomRate = zoomRate - zoomInterval;
            // setZoom(zoomRate);
        }
    }
    event.preventDefault();
})

function setZoom(z) {
    var p = [ "-webkit-", "-moz-", "-ms-", "-o-", "" ],
        s = "scale(" + z + ")";

    for (var i = 0; i < p.length; i++)
        $('#right-panel').css(p[i] + "transform", s);
};
*/

$('#btn_delete_project').bind('click', function() {
    var projectId = getURLParameter('project_id');
    bootbox.dialog({
        'message': 'Are you sure to delete this project?',
        'buttons': {
            'confirm': {
                'label': 'Yes',
                'className': 'btn-danger',
                callback: function() {
                    $.post(
                        '/project/delete',
                        {
                            'project_id': projectId
                        },
                        function(r) {
                            if (r.status > 0) {
                                bootbox.dialog({
                                    message: 'delete successfully',
                                    buttons: {
                                        success: {
                                            label: 'OK',
                                            callback: function() {
                                                document.location.href = '/project/index';
                                            }
                                        }
                                    }
                                });
                            } else {
                                bootbox.alert('Error: delete failed');
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

$('#btn_edit_permission').bind('click', function() {
    var projectId = getURLParameter('project_id');
    document.location.href = "/project/permission/index?project_id=" + projectId;
})

$('#name_edit').bind('click', function() {
    var name = $('#label_name').text();
    $('#label_name').hide();
    $('#input_name').val(name);
    $('#input_name').show();
    $('#name_edit').hide();
    $('#name_submit').show();
})

$('#name_submit').bind('click', function() {
    var projectId = getURLParameter('project_id');
    var name = $('#input_name').val();

    $.ajax({
        url: '/project/rename',
        type: 'POST',
        data: {
            'project_id': projectId,
            'name': name
        },
        success: function(r) {
            if (r.status > 0) {
                $('#label_name').text(name);
                $('#label_name').show();
                $('#input_name').hide();
                $('#name_submit').hide();
                $('#name_edit').show();
            } else {
                bootbox.alert("Error: " + r.error);
            }
        },
        async: false
    })
})