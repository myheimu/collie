/**
 * Created by haibin on 14-9-17.
 */

var currentSelectedPath = "/";

$(document).ready(function() {
    appendFolder(1, "/");

    $(".item-folder").bind('click', function() {
        var currentFolderValue = $(this).attr("name");
        var parentFolder = $(this).parents(".folder");
        var parentDepth = parseInt(parentFolder.attr("depth"));
        var parentPath = parentFolder.attr("path");

        // shrink descendant folders
        $(".folder").filter(function() {
            return parseInt($(this).attr("depth")) > parentDepth;
        }).remove();

        // change icon
        parentFolder.find("span").filter(function() {
            return $(this).hasClass("icon-folder-open");
        }).removeClass("icon-folder-open").addClass("icon-folder-close").parent().removeClass("active");
        $(this).addClass("active").children("span").removeClass("icon-folder-close").addClass("icon-folder-open");

        // get sub items, and append folder
        var currentPath = parentPath + currentFolderValue + "/";
        var folder = appendFolder(parentDepth + 1, currentPath);

        // set current selected path
        currentSelectedPath = currentPath;
    });

    $('#preview_btn').bind('click', function() {
        // get current selected path
        console.info("current selected path: %s", currentSelectedPath);

        // get content from current selected path (from preview API)
        $.get("file_preview",
            {
                'path': currentSelectedPath,
                'column_delimiter': $("#column_delimiter").val() // TODO
            },
            function(r) {
                if (r.status > 0) {
                    var previewTable = r.table_data;
                    var tableJson = JSON.parse(previewTable);
                    var head = tableJson.head;
                    var body = tableJson.body;

                    console.info("head: " + head);
                    console.info("body: " + body);

                    // clear table
                    $("#preview_table thead #tr_column_names td[id!='table_column_name_temp']").remove();
                    $("#preview_table thead #tr_column_types td[id!='table_column_type_temp']").remove();
                    $("#preview_table tbody tr[id!='table_row_temp']").remove();

                    for (var headIndex in head) {
                        var column = head[headIndex];
                        // column name
                        var columnName = $("#table_column_name_temp").clone(true, true);
                        $(columnName).attr("id", "");
                        $(columnName).children("input").val(column);
                        $("#tr_column_names").append(columnName);
                        columnName.show();
                        // column type
                        var columnType = $("#table_column_type_temp").clone(true, true);
                        $(columnType).attr("id", "");
                        $("#tr_column_types").append(columnType);
                        columnType.show();
                    }

                    var rowCount = 0;
                    for (var rowIndex in body) {
                        var tableRow = $("#table_row_temp").clone(true, true);
                        $(tableRow).attr("id", "");
                        var row = body[rowIndex]
                        for (var headIndex in head) {
                            var columnKey = head[headIndex];
                            var tableRowCell = $("#table_row_cell_temp").clone(true, true);
                            $(tableRowCell).attr("id", "");
                            if (row[columnKey] != undefined) {
                                tableRowCell.html(row[columnKey]);
                            } else {
                                tableRowCell.html("");
                            }
                            tableRow.append(tableRowCell);
                            tableRowCell.show();
                        }
                        $("#table_body").append(tableRow)
                        tableRow.show();

                        if (++rowCount > 10) break;
                    }
                }
            }
        )

    })
});

function appendItemFolder(parentFolder, folderName) {
    var itemFolder = $("#item_folder_temp").clone(true, true);
    itemFolder.attr("id", "");
    itemFolder.attr("name", folderName);
    itemFolder.children(".name").text(truncateName(folderName));
    itemFolder.appendTo(parentFolder.children("ul"));
    itemFolder.show();
}

function appendItemFile(parentFolder, fileName) {
    var itemFile = $("#item_file_temp").clone(true, true);
    itemFile.attr("id", "");
    itemFile.attr("name", fileName);
    itemFile.children(".name").text(truncateName(fileName));
    itemFile.appendTo(parentFolder.children("ul"));
    itemFile.show();
}

function truncateName(fileName) {
    var maxLen = 16;
    if (fileName.length > maxLen) {
        return fileName.substr(0, maxLen) + "...";
    } else {
        return fileName;
    }
}

function appendFolder(depth, path) {
    $("#progress").show();

    var folder = $("#folder_temp").clone(true, true);
    folder.attr("depth", depth);
    folder.attr("path", path);
    folder.css({"top": "0px", "left": ((depth-1) * 200) + "px"});

    // do GET to webHDFS api
    $.ajax({
        type: 'GET',
        url: '/table/file_list',
        data: {
            'path': path
        },
        success: function(r) {
            if (r.status > 0) {
                var listData = r.data;
                for (var dataIndex in listData) {
                    var item = listData[dataIndex];
                    var itemType = item['type'];
                    var itemName = item['name'];
                    if (itemType == 'FILE') {
                        appendItemFile(folder, itemName);
                    } else if (itemType == 'DIRECTORY') {
                        appendItemFolder(folder, itemName);
                    }
                }

                $("#progress").hide();
            } else {
                $("#progress").hide();
            }
        },
        async: true
        }
    );

    folder.appendTo($(".file-browser"));
    folder.show();
    return folder;
}




