
$(document).ready(function(){
	$('.data-table').dataTable({
		"bJQueryUI": true,
        "aLengthMenu": [[10, 25, 50, 100], [10, 25, 50, 100]],
        "iDisplayLength" : 50,
		"sPaginationType": "full_numbers",
		// "sDom": '<""l>t<"F"fp>',
		"sDom": '<"top"flp>rt<"bottom"i><"clear">',
        // If sorting is enabled, then DataTables will perform a first pass sort on initialisation.
        // You can define which column(s) the sort is performed upon, and the sorting direction, with this variable.
        // The aaSorting array should contain an array for each column to be sorted initially containing the column's index and a direction string ('asc' or 'desc').
        "aaSorting": []
	});

	$('input[type=checkbox],input[type=radio],input[type=file]').uniform();
	
	$('select').select2();
	
	$("span.icon input:checkbox, th input:checkbox").click(function() {
		var checkedStatus = this.checked;
		var checkbox = $(this).parents('.widget-box').find('tr td:first-child input:checkbox');		
		checkbox.each(function() {
			this.checked = checkedStatus;
			if (checkedStatus == this.checked) {
				$(this).closest('.checker > span').removeClass('checked');
			}
			if (this.checked) {
				$(this).closest('.checker > span').addClass('checked');
			}
		});
	});	
});
