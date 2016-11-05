/**
 * Created by haibin on 14-10-22.
 */

$(document).ready(function(){
    $.get(
        '/data/hello_world',
        {},
        function(r) {
            $("#text_from_server").html(r.data);
        })
})