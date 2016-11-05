/**
 * Created by haibin on 14-4-28.
 */

var uploadBy = "local";
var newGitFile = {hasNew: false};
var resumable;

$(document).ready(function() {
    $("#newModuleModal").on('shown.bs.modal', function() {
        var moduleModalMode = $(document).data('modalMode');
        var uploadMode = $(document).data('uploadMode');
        if(uploadMode == "git_only"){
            $("#local_btn").attr("disabled","disabled");
            $("#git_btn").button('toggle');
            fromGit();
        }else{
            if(uploadMode == "local_only"){ $("#git_btn").attr("disabled","disabled"); }
            $("#local_btn").button('toggle');
            fromLocal();
        }
        if (moduleModalMode == 'update') {
            var moduleId = $(document).data('moduleId');
            var moduleVersion = $(document).data('moduleVersion');

            $('#myModalLabel').text('Update Module');
            $('#control_group_description').hide();
            $('#control_group_wiki_link').hide();

            $.ajax({
                url: '/module/detail',
                data: {
                    'module_id': moduleId,
                    'module_version': moduleVersion
                },
                success: function(r) {
                    // module name
                    var moduleName = r.name;
                    $('#module_name').val(moduleName);
                    $('#module_name').prop('disabled', true);

                    // no version found
                    if (r.latest_type == "") {
                        return;
                    }

                    // latest version type
                    var type = r.latest_type;
                    $('#version_type').val(type);
                    $('#version_type').select2();

                    /** setup: File Upload **/
                    // latest version file name
                    var fileName = r.latest_file_name;

                    $('#newModuleModal #upload_git').show();
                    if(r.git_options){
                        $('#newModuleModal #file_upload_keep_old').hide();
                        $('#newModuleModal #file_upload_go_keep_old').hide();
                        $('#newModuleModal #file_upload_renew').show();
                        r.git_options["latest_file_name"] = fileName
                        $(document).data("gitOptions",r.git_options);
                        $("#git_btn").button('toggle');
                        fromGit();
                        resetGitOptions();
                    }else{
                        $('#newModuleModal #file_upload_renew').hide();
                        $('#newModuleModal #file_upload_go_keep_old').hide();
                        $('#newModuleModal #file_upload_keep_old').show();
                        $('#newModuleModal .old_file_name').text(fileName);
                        $('#newModuleModal #git_reset_btn').hide();
                    }

                    // latest version options
                    var options = r.latest_options;
                    if (options.hadoop_support) {
                        $('#check_hadoop_support').attr('checked', 'checked');
                        $('#check_hadoop_support').parent().addClass('checked');
                    }

                    var selectedOption = $('#version_type option:selected');
                    $('.options_div').hide();
                    var optionsTarget = selectedOption.attr('options_target');
                    $('#' + optionsTarget).show();
                    var supportFileType = selectedOption.attr('support_file_type');
                    $('#fileToUpload').prop('accept', supportFileType);
                    $('.option[id!=option_temp]').remove();
                    if (type == 'Shell') {
                        var args = options['args'];
                        for (var argIndex in args) {
                            var arg = args[argIndex];
                            addOption('shell_args', arg);
                        }
                        $('#input_main_script').val(options['main_script']);
                    } else if (type == 'Jar') {
                        var args = options['jvm_args'];
                        for (var argIndex in args) {
                            var arg = args[argIndex];
                            addOption('jar_properties', arg);
                        }
                        var args = options['main_args'];
                        for (var argIndex in args) {
                            var arg = args[argIndex];
                            addOption('jar_arguments', arg);
                        }
                        $('#input_java_class').val(options['java_class']);
                        $('#input_classpath').val(options['classpath']);
                        $('#input_Xms').val(options['Xms']);
                        $('#input_Xmx').val(options['Xmx']);
                    } else if (type == 'yarn') {
                        var args = options['jvm_args'];
                        for (var argIndex in args) {
                            var arg = args[argIndex];
                            addOption('yarn_properties', arg);
                        }
                        var args = options['main_args'];
                        for (var argIndex in args) {
                            var arg = args[argIndex];
                            addOption('yarn_arguments', arg);
                        }
                        $('#input_main_class').val(options['main_class']);
                    } else if (type == 'spark') {
                        var args = options['spark_args'];
                        for (var argIndex in args) {
                            var arg = args[argIndex];
                            addOption('spark_arguments', arg);
                        }
                        $('#input_spark_class').val(options['spark_class']);
                    }
                },
                async:true
            })
        } else { // new
            $('#newModuleModal #file_upload_keep_old').hide();
            $('#newModuleModal #file_upload_go_keep_old').hide();
            $('#newModuleModal #file_upload_renew').show();
            $('#newModuleModal #upload_git').show();
            $('#newModuleModal #git_reset_btn').hide();
            clearUpload();
        }
    });

    /** js for file chunks uploading **/
    resumable = new Resumable({
        target: '/module/upload',
        chunkSize: 126 * 1024,
        simultaneousUploads:1,
        testChunks: true,
        throttleProgressCallbacks:1,
        method: "octet",
        maxFiles: 1
    });
    resumable.assignBrowse($("#fileToUpload"));
    // once file added, we will start to upload file
    resumable.on('fileAdded', function(file) {
        console.log("file is added");
        // check uploading file type
        var fileAccept = $('#fileToUpload').prop('accept');
        if (file.fileName.slice(-fileAccept.length) != fileAccept) {
            // show error message
            $('.resumable-list').html('<li class="resumable-file-'+file.uniqueIdentifier+'">Could not upload <span class="resumable-file-name"></span><span class="resumable-file-progress"></span>')
            $('.resumable-file-'+file.uniqueIdentifier+' .resumable-file-name').html(file.fileName);
            $('.resumable-file-' + file.uniqueIdentifier + ' .resumable-file-progress').html(' (only ' + fileAccept +' is acceptable)');
            $('.progress-resume-link, .progress-pause-link').hide();
            return;
        }
        // Show progress bar
        $('.resumable-progress, .resumable-list').show();
        // Show pause, hide resume
        $('.resumable-progress .progress-resume-link').hide();
        $('.resumable-progress .progress-pause-link').show();
        // Add the file to the list
        $('.resumable-list').html('<li class="resumable-file-'+file.uniqueIdentifier+'">Uploading <span class="resumable-file-name"></span><span class="resumable-file-progress"></span>')
        $('.resumable-file-'+file.uniqueIdentifier+' .resumable-file-name').html(file.fileName);
        // Actually start the upload
        resumable.upload();
    });
    resumable.on('pause', function () {
        // Show resume, hide pause
        $('.resumable-progress .progress-resume-link').show();
        $('.resumable-progress .progress-pause-link').hide();
    });
    resumable.on('complete', function () {
        // Hide pause/resume when the upload has completed
        $('.resumable-progress .progress-resume-link, .resumable-progress .progress-pause-link').hide();
    });
    resumable.on('fileSuccess', function (file, message) {
        // Reflect that the file upload has completed
        $('.resumable-file-' + file.uniqueIdentifier + ' .resumable-file-progress').html(' (completed)');
    });
    resumable.on('fileError', function (file, message) {
        // Reflect that the file upload has resulted in error
        $('.resumable-file-' + file.uniqueIdentifier + ' .resumable-file-progress').html(' (file could not be uploaded: ' + message + ')');
    });
    resumable.on('fileProgress', function(file){
        // Handle progress for both the file and the overall upload
        $('.resumable-file-' + file.uniqueIdentifier + ' .resumable-file-progress').html(' ' + Math.floor(file.progress() * 100) + '%');
        $('.progress-bar').css({width: Math.floor(resumable.progress() * 100) + '%'});
    });

    function addOption(appendTargetId, optionInfo) {
        var optionDiv = $("#option_temp").clone(true, true);
        optionDiv.show();
        optionDiv.attr('id', '');
        optionDiv.children('.input_option_name').val(optionInfo['name']);
        optionDiv.children('.input_option_default').val(optionInfo['default']);
        optionDiv.children('.input_option_description').val(optionInfo['description']);
        optionDiv.appendTo($('#' + appendTargetId));
    };

    $('#go_upload_new_file').bind('click', function() {
        $('#file_upload_keep_old').hide();
        $('#file_upload_renew').show();
        $('#file_upload_go_keep_old').show();
    });

    $('#go_keep_old').bind('click', function() {
        $('#file_upload_renew').hide();
        $('#file_upload_go_keep_old').hide();
        $('#file_upload_keep_old').show();
    });

    $(".btn_add_option").bind("click", function(){
        var appendTargetId = $(this).attr('append_target');
        var optionDiv = $("#option_temp").clone(true, true);
        optionDiv.show();
        optionDiv.attr('id', '');
        optionDiv.appendTo($('#' + appendTargetId));
    });

    $('.btn_delete_option').bind('click', function() {
        var option = $(this).parents('.option');
        option.remove();
    });

    $('#version_type').change(function() {
        var selectedOption = $(this).children('option:selected');
        var optionsTarget = selectedOption.attr('options_target');
        var supportFileType = selectedOption.attr('support_file_type');
        $('.options_div').hide();
        $('#' + optionsTarget).show();
        $('#fileToUpload').prop('accept', supportFileType);
    });

    $('#btn_save').bind('click', function() {
        var moduleModalMode = $(document).data('modalMode');
        if (!moduleModalMode) {moduleModalMode = 'new';}

        var moduleName = $("#module_name").val();
        var moduleDescription = $('#module_description').val();
        var moduleWikiLink = $('#module_wiki_link').val();
        var versionType = $('#version_type :selected').val();
        var versionFile;
        var versionFileIdentifier = "";
        if (moduleModalMode == 'new' && (moduleName == '' || moduleDescription == '')) {
            bootbox.alert('Error: Please fill in required information');
            return;
        }

        if (moduleModalMode == 'update' && (moduleName == '')) {
            bootbox.alert('Error: Please fill in required information');
            return;
        }

        var gitOptions = ""
        var keepOldFile = false;
        if (uploadBy == "local") {
            var uploadSucceed = false;
            if (resumable.files.length > 0) {
                var file = resumable.files[0];
                if (file.isComplete()) {
                    uploadSucceed = true;
                }
            }
            if ($('#file_upload_renew').is(':visible') && !uploadSucceed) {
                bootbox.alert('Error: Please upload file.');
                return;
            }
            if ($('#file_upload_renew').is(':visible')) {
                versionFile = resumable.files[0].fileName;
                versionFileIdentifier = resumable.files[0].uniqueIdentifier;
            } else {
                versionFile = $($(".old_file_name")[0]).text();
                keepOldFile = true;
            }
        } else if(uploadBy == "git"){
            if(!newGitFile.hasNew && moduleModalMode=="new"){
                bootbox.alert('Error: Please upload file.');
                return;
            }
            if($("#git_build_btn").text() == "Building..."){
                bootbox.alert('Error: Please wait build complete.');
                return;
            }
            gitOptions={};
            gitOptions.repository = $("#git_repo").val();
            gitOptions.branch = $("#git_branch").val();
            gitOptions.version = $("#git_history").val();
            gitOptions.build = $("#git_build").val();
            for(var item in gitOptions){
                if(newGitFile[item] != gitOptions[item]){
                    bootbox.alert('Error: You have changed git options.Please upload file or reset.');
                    return;
                }
            }
            if(!newGitFile.hasNew){
                keepOldFile = true;
            }
            versionFile = newGitFile.fileName;
        }
        var options = {}
        if (versionType == 'Shell') {
            var hadoopSupport = $('#check_hadoop_support').attr('checked') == 'checked';
            var mainScript = $('#input_main_script').val();
            var args = getOptions('shell_args');
            options = {
                'hadoop_support': hadoopSupport,
                'main_script': mainScript,
                'args': args
            }
        } else if (versionType == 'Jar') {
            var javaClass = $('#input_java_class').val();
            var classpath = $('#input_classpath').val();
            var xms = $('#input_Xms').val();
            var xmx = $('#input_Xmx').val();
            var jvmArgs = getOptions('jar_properties');
            var mainArgs = getOptions('jar_arguments');
            options = {
                'java_class': javaClass,
                'classpath': classpath,
                'Xms': xms,
                'Xmx': xmx,
                'jvm_args': jvmArgs,
                'main_args': mainArgs
            }
        } else if (versionType == 'yarn') {
            var mainClass = $('#input_main_class').val();
            var jvmArgs = getOptions('yarn_properties');
            var mainArgs = getOptions('yarn_arguments');
            options = {
                'main_class': mainClass,
                'jvm_args': jvmArgs,
                'main_args': mainArgs
            }
        } else if (versionType == 'spark') {
            var sparkClass = $('#input_spark_class').val();
            var sparkArgs = getOptions('spark_arguments');
            options = {
                'spark_class': sparkClass,
                'spark_args': sparkArgs
            }
        }

        var moduleModalMode = $(document).data('modalMode');
        if (moduleModalMode == 'update') {
            var moduleId = $(document).data('moduleId');
            $.ajax({
                    url: "/module/version/new",
                    type: 'POST',
                    data: {
                        "module_id": moduleId,
                        "type": versionType,
                        "file": versionFile,
                        "file_identifier": versionFileIdentifier,
                        "keep_old_file": keepOldFile,
                        "options": JSON.stringify(options),
                        "git_options": !gitOptions || gitOptions==""?"":JSON.stringify(gitOptions)
                    },
                    success: function(r) {
                        if (r.status > 0) {
                            var moduleId = r.module_id;
                            document.location.href = '/module/manage?module_id=' + moduleId;
                        } else {
                            bootbox.alert('Error: ' + r.error);
                        }
                    },
                    complete: function(r) {
                        closeModal('module_saving_fade', 'module_saving_modal');
                    },
                    async:true
                }
            );
        } else {
            $.ajax({
                    url: "/module/save",
                    type: 'POST',
                    data: {
                        "name": moduleName,
                        "description": moduleDescription,
                        "wiki_link": moduleWikiLink,
                        "type": versionType,
                        "file": versionFile,
                        "file_identifier": versionFileIdentifier,
                        "options": JSON.stringify(options),
                        "git_options": !gitOptions || gitOptions==""?"":JSON.stringify(gitOptions)
                    },
                    success: function(r) {
                        if (r.status > 0) {
                            var moduleId = r.module_id;
                            document.location.href = '/module/manage?module_id=' + moduleId;
                        } else {
                            bootbox.alert('Error: ' + r.error);
                        }
                    },
                    complete: function(r) {
                        closeModal('module_saving_fade', 'module_saving_modal');
                    },
                    async:true
                }
            );
        }
    });

    $('#git_repo').select2({placeholder: "Select a repository"})
        .on("change",function(e){
            var gitOptions = $(document).data("gitOptions")
            if(gitOptions && $("#git_repo").val() == gitOptions.repository)
                getGitHistory({
                    repository: gitOptions.repository,
                    version: gitOptions.version,
                    build: gitOptions.build
                });
            else
                getGitHistory({repository: e.val});
        })
    $("#git_history").select2()
        .on("change", function(e){
            getGitBuildName({
                repository: $("#git_repo").val(),
                branch: 'master',
                version: e.val
            })
        });
})

function getOptions(optionsId) {
    var options = []
    $("#" + optionsId + " .option[id!=option_temp]").each(function(index){
        var optionName = $(this).children('.input_option_name').val();
        var optionDefault = $(this).children('.input_option_default').val();
        var optionDescription = $(this).children('.input_option_description').val();
        options.push({
            'name': optionName,
            'default': optionDefault,
            'description': optionDescription
        });
    });
    return options;
}

function clearUpload() {
    $('#newModuleModal .filename').text('No file selected');
    $('#gitUploadResult').text('');
    $('#git_repo').select2("val","");
    $('#git_history').empty();
    $('#git_history').select2();
    $('#git_build').empty();
    $('#git_build').select2();
}

function getGitHistory(options) {
    $("#git_history").empty();
    $("#module_saving_modal").show();
    var repository = options.repository ? options.repository : null;
    var version = options.version ? options.version : null;
    var build = options.build ? options.build : null;
    $.ajax({
            url: "/module/git/history",
            type: 'GET',
            data: {
                "repository": repository
            },
            success: function(r) {
                if (r.status > 0) {
                    var select = "";
                    for(var i in r.history){
                        var str = r.history[i];
                        if(i == 0){
                            str += " [head]"
                            select=r.history[i];
                        }
                        if(version && r.history[i] == version){
                            str += " [now]"
                            select=r.history[i];
                        }
                        var innerHtml = "<option value='" + r.history[i] +"'>" + str + "</option>";
                        $("#git_history").append(innerHtml);
                    }
                    if(version && select!=version){
                        select=version;
                        var innerHtml = "<option value='" + version +"'>" + str + " [now]</option>";
                        $("#git_history").append(innerHtml);
                    }
                    $("#git_history").select2("val",select);
                    $("#module_saving_modal").hide();
                    getGitBuildName({
                        repository: $("#git_repo").val(),
                        branch: 'master',
                        version: select,
                        build: build
                    })
                } else {
                    bootbox.alert('Error: ' + r.error);
                    $("#module_saving_modal").hide();
                }
            },
            async:true
        }
    );
}

function getGitBuildName(options) {
    $("#module_saving_modal").show();
    $('#gitUploadResult').text('');
    $("#git_build").empty();
    $("#git_build").select2();
    var repository = options.repository ? options.repository : null;
    var version = options.version ? options.version : null;
    var build = options.build ? options.build : null;
    $.ajax({
            url: "/module/git/build",
            type: 'GET',
            data: {
                "repository": repository,
                "version": version
            },
            success: function(r) {
                if (r.status > 0) {
                    var select = "";
                    for(var i in r.buildList){
                        var str = r.buildList[i];
                        if(version && r.buildList[i] == build){
                            str += " [now]"
                            select=r.buildList[i];
                        }
                        var innerHtml = "<option value='" + r.buildList[i] +"'>" + str + "</option>";
                        if(r.buildList[i].toLowerCase() == "default")
                            $("#git_build").prepend(innerHtml);
                        else
                            $("#git_build").append(innerHtml);
                    }
                    if(select != "")
                        $("#git_build").val(select);
                    $("#git_build").select2();
                } else {
                    bootbox.alert('Error: ' + r.error);
                }
            },
            complete: function() {
                $("#module_saving_modal").hide();
            },
            async:true
        }
    );
}

function fromLocal(){
    $("#from_git_panel").hide();
    $("#from_local_panel").show();
    uploadBy = "local"
}

function fromGit(){
    $("#from_local_panel").hide();
    $("#from_git_panel").show();
    uploadBy = "git"
}

//function saveRepo(){
//    var repo = $("#git_repo_edit input").val();
//    if(repo.trim() == ""){
//        bootbox.alert("Error: The repository can't be blank");
//        return;
//    }
//    getGitHistory({"repository":repo});
//}
//
//function unsaveRepo(){
//    $("#git_repo_edit").hide();
//    $("#git_repo").show();
//}

function gitBuild(){
    var repo = $("#git_repo").select2("val");
    var branch = $("#git_branch").val();
    var version = $("#git_history").select2("val");
    var build = $("#git_build").select2("val");
    if(!version || !build || repo == "") {
        bootbox.alert("Error: Git options are not complete!");
        return;
    }
    $('#gitUploadResult').text('');
    $("#git_build_btn").text("Building...")
    $("#git_build_btn").attr("disabled","disabled");
    $.ajax({
            url: "/module/git/upload",
            type: 'POST',
            data: {
                "repository": repo,
                "branch": branch,
                "version": version,
                "build": build
            },
            success: function(r) {
                if (r.status > 0) {
                    newGitFile = {
                        hasNew: true,
                        fileName: r.file_name,
                        repository: repo,
                        branch: branch,
                        version: version,
                        build: build
                    }
                    $('#gitUploadResult').text('success');
                    $('#gitUploadResult').css('color', 'green');
                } else {
                    //bootbox.alert('Error: ' + r.error);
                    $('#gitUploadResult').text(r.error);
                    $('#gitUploadResult').css('color', 'red');
                }
            },
            complete: function(r) {
                $("#git_build_btn").removeAttr("disabled");
                $("#git_build_btn").text("Build");
            },
            async:true
        }
    );
}

function resetGitOptions(){
    $('#gitUploadResult').text('');
    var gitOptions = $(document).data("gitOptions");
    $("#git_repo_edit").hide();
    $("#gitUploadResult").text();
    $("#git_branch").val(gitOptions.branch);
    newGitFile = {
        hasNew: false,
        repository: gitOptions.repository,
        branch: gitOptions.branch,
        version: gitOptions.version,
        build: gitOptions.build,
        fileName: gitOptions.latest_file_name
    }
    $("#git_repo").val(gitOptions.repository).change();
}