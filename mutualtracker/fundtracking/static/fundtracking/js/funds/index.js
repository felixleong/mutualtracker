$(function() {
    // Plotting sparklines
    $('div.sparkline').each(function(i) {
        $.plot(
            $(this),
            [ {
		data: fundPrices[i],
                color: '#070'
	    } ],
            {
                grid: { borderWidth: 0 },
                series: {
		    lines: { fill: true, lineWidth: 1 },
                    shadowSize: 0
                },
                xaxis: { ticks: [] },
                yaxis: { ticks: [], autoscaleMargin: 0.1 }
            });
    });

    // Advanced table functions: Search, filter and paginate
    $('#fund-index-table').dataTable({
	// Features
	bAutoWidth: true,
	bLengthChange: false,

	// Options
	aoColumns: [
	    { sType: 'html' }, { sType: 'html' }, // Code, Name
	    { bSearchable: false, bSortable: false }, // Date
	    { bSearchable: false }, // NAV
	    { bSearchable: false, bSortable: false }, // 52-wk range
	    { bSearchable: false, bSortable: false } // Sparkline
	],
	asStripClasses: ['altrow', '']
	});
});
