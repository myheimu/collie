/**
 * Created by haibin on 14-6-6.
 */

$(document).ready(function() {
    $("#file-uploader").uploadify({
        'uploader' : '/static/uploadify/uploadify.swf',
        'cancelImg' : '/static/uploadify/cancel.png',
        'script'    : '/module/upload',
        'folder'    : '/upload', // folder是上传文件的目录，这里我们不计划使用它，随便写一个充数。
        'fileDesc' : 'Upload Files',
        'fileExt' : '*.keytab',
        'auto'      : true,//
        'multi': false,
        'onInit': function () {
            $("#file-upload-cancel").hide();
        },
        'onError' : function (event,ID,fileObj,errorObj) {
            obj = errorObj;
        },
        'onSelect': function (e, queueId, fileObj) {
        },
        'onAllComplete': function (event, data) {
            $("#file-upload-cancel").hide();
            if (data.filesUploaded >=1){
            } else {
                $('#version_file').html("Failed");
                $('#version_file').css('color', 'red');
            }
        },
        'onComplete': function (event, queueId, fileObj, response, data) {
            $('#version_file').html(fileObj.name);
            $('#version_file').css('color', 'black');
        },
        'onProgress': function () {
            $("#file-upload-cancel").show();
        }
    });

    $('#btn_save').bind('click', function() {
        var keyName = $('#key_name').val();
        var fileName = $('#newKerberosKey .filename').text();

        $.ajax({
                url: "/profile/save_kerberos",
                type: 'POST',
                data: {
                    "name": keyName,
                    "file": fileName
                },
                success: function(r) {
                    if (r.status > 0) {
                        document.location.href = '/profile/kerberos';
                    } else {
                        bootbox.alert('Error: ' + r.error);
                    }
                },
                async: false
            }
        );
    })

    $('.btn_delete').bind('click', function() {
        var keyName = $(this).attr('key_name');

        $.ajax({
            url: "/profile/delete_kerberos",
            type: 'POST',
            data: {
                "name": keyName
            },
            success: function(r) {
                if (r.status > 0) {
                    document.location.href = '/profile/kerberos';
                } else {
                    bootbox.alert('Error: ' + r.error);
                }
            },
            async: false
            }
        );
    })
})

$('#newKerberosKey').on('shown.bs.modal', function() {
    clearUpload();
})

function fileSelected() {
    var file = document.getElementById('fileToUpload').files[0];
    // var file = $('#fileToUpload').files[0];
    if (file) {
        var fileSize = 0;
        if (file.size > 1024 * 1024)
            fileSize = (Math.round(file.size * 100 / (1024 * 1024)) / 100).toString() + 'MB';
        else
            fileSize = (Math.round(file.size * 100 / 1024) / 100).toString() + 'KB';

        $('#fileName').text('Name: ' + file.name);
        $('#fileSize').text('Size: ' + fileSize);
        $('#fileType').text('Type: ' + file.type);
    }
}

function uploadFile() {
    var xhr = new XMLHttpRequest();
    var fd = new FormData();
    var files = document.getElementById('fileToUpload').files;
    if (null == files || files.length <= 0) {
        $('#uploadResult').text('please select file first');
        $('#uploadResult').css('color', 'red');
        return;
    }

    fd.append("Filedata", files[0]);

    /* event listners */
    xhr.upload.addEventListener("progress", uploadProgress, false);
    xhr.addEventListener("load", uploadComplete, false);
    xhr.addEventListener("error", uploadFailed, false);
    xhr.addEventListener("abort", uploadCanceled, false);

    /* Be sure to change the url below to the url of your upload server side script */
    xhr.open("POST", "/profile/upload_kerberos");
    xhr.send(fd);
}

function uploadProgress(evt) {
    if (evt.lengthComputable) {
        var percentComplete = Math.round(evt.loaded * 100 / evt.total);
        $('#progressNumber').text(percentComplete.toString() + '%');
    }
    else {
        $('#progressNumber').text('unable to compute');
    }
}

function uploadComplete(evt) {
    $('#uploadResult').text('success');
    $('#uploadResult').css('color', 'green');
}

function uploadFailed(evt) {
    $('#uploadResult').text('failed');
    $('#uploadResult').css('color', 'red');
}

function uploadCanceled(evt) {
    bootbox.alert("The upload has been canceled by the user or the browser dropped the connection.");
}

function clearUpload() {
    $('#newKerberosKey .filename').text('No file selected');
    $('#fileName').text('');
    $('#fileSize').text('');
    $('#fileType').text('');
    $('#progressNumber').text('');
    $('#uploadResult').text('');
}