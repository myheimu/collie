/**
 * Created by haibin on 14-3-6.
 */

$(document).ready(function(){
    $('#sidebar li').removeClass('active');
    $('#bar-projects').addClass('active');
    $('#table_id2').dataTable();
})

$("#create-project").bind("click", function() {
    var project_name = "hello";
    document.location.href = "/project/new?project_name=" + project_name;
})

$("#btn_create_project").bind("click", function() {
    console.log("click button create project");

    // get project name
    var projectName = $("#project_name").val();
    if (!projectName || projectName.length === 0) {
        alert("please fill in project name");
        return;
    }

    // do post to new a project
    $.post(
        '/project/new',
        {
            'project_name': projectName
        },
        function(r) {
            if (r.status) {
                document.location.href = "/project/edit?project_id=" + r.project_id;
            } else {
                alert('create project failed');
            }
        }
    )
});

$("#createProjectModal").on('hidden.bs.modal', function()
    {
        console.log("echo >> closing modal");
        $("#project_name").val("");
    }
);
