PriceChart = function(chartElem, overviewElem) {
    // Element handles
    this._chartElem = chartElem;
    this._overviewElem = overviewElem;
    this._legendElem = null;
    this._legendLabelElem = null;
    this._overlay = null;

    // Chart instances
    this._chart = null;
    this._overview = null;
    this._hoverLegend =
	'<span class="price-legend-date">00 Month 0000</span>: 0.0000';

    // Flot chart options
    this._chartOptions =
        {
	    crosshair: { mode: 'x' },
	    grid: { hoverable: true },
            xaxis: {
                minTickSize: [7, "day"],
                mode: "time",
                timeformat: "%d %b %y"
            },
            yaxis: {
                autoscaleMargin: 0.05
            }
        };
    this._overviewOptions =
	{
	    selection: { mode: 'x' },
	    series: {
		lines: { lineWidth: 1 },
		shadowSize: 0
	    },
	    xaxis: {
		mode: 'time',
		tickSize: [1, "year"],
		timeformat: "%y"
	    },
	    yaxis: {
		min: 0,
		ticks: [],
		autoscaleMargin: 0.1
	    }
	};

    // Event-related members
    this._overviewStartDate = null;
    this._latestPosition = null;
    this._updateLegendTimeout = null;
    this._chartData = null;
    this._updatingChart = false;
    this._previousSelection = null;
    this._priceHistoryUrl = '/prices/history';
//    this._priceHistoryUrl = '/~felix/PBTracker/prices/history';

    // Bind neccessary events
    this._createLoadingOverlay();
    this._bindEvents();
}
$.extend(PriceChart.prototype, {
    plotChart: function(chartData)
    {
	this._chart = $.plot(
	    this._chartElem,
	    [{ label: this._hoverLegend, data: chartData }],
	    this._chartOptions);

	// Regrab the legend elements
	this._legendElem = $('.legend', this._chartElem);
	this._legendLabelElem = $('.legendLabel', this._legendElem);

	// Preset the legend label properties then hide
	this._legendLabelElem
		.css({
		    textAlign: 'right',
		    width: this._legendLabelElem.width() + 10 + 'px'
		});
	this._legendElem.hide();
    },

    plotOverview: function(overviewData)
    {
	this._overviewStartDate = overviewData[overviewData.length - 1][0];

	// Add some extra options
	overviewOptions = $.extend(true, this._overviewOptions, {
		grid: {
		    markings: [{
			color: '#dec',
			xaxis: { to: this._overviewStartDate }
		    }]
		},
		xaxis: { min: overviewData[0][0] - 2.529144e+11 } // 8 years 
	    });

	this._overview = $.plot(
	    this._overviewElem, [ overviewData ], overviewOptions);
    },

    setLegend: function(date, nav)
    {
	var newLegend = this._hoverLegend;
	newLegend = newLegend.replace(/00 Month 0000/, toShortDate(date));
	newLegend = newLegend.replace(/:.*/, ': ' + nav.toFixed(4));

	this._legendLabelElem.html(newLegend);
    },

    _updateLegend: function()
    {
        this._updateLegendTimeout = null;
	var pos = this._latestPosition;
        var axes = this._chart.getAxes();
	if(pos.x < axes.xaxis.min || pos.x > axes.xaxis.max ||
	    pos.y < axes.yaxis.min || pos.y > axes.yaxis.max)
	{
	    return;
	}

	// Find the nearest point, x-wise
	// *NOTE: Our dataset is ordered in reverse (i.e. latest first)
	var series = this._chart.getData()[0];
	var priceDate = 0;
	var nav = 0.0;
	for(var i = 0; i < series.data.length; i++) {
	    if(series.data[i][0] <= pos.x)
	    {
		priceDate = series.data[i][0];
		nav = series.data[i][1];
		break;
	    }
	}

	this.setLegend(priceDate, nav);
    },

    _fetchData: function(from, to, callback)
    {
	var params = {
	    since: toISO8601DateString(from),
	    until: toISO8601DateString(to)
	};
	var toDate = parseDate(toISO8601DateString(to));
	var self = this;
	$.getJSON(
	    this._priceHistoryUrl + '/' + fundCode +
		generateCakePhpUrlParameters(params) + '.json',
	    {},
	    function(data) {
		if(data.length > 0) {
		    var firstDate = parseDate(data[0].date);
		    var dataArray = [];
		    $.each(data, function(key, elem) {
			dataArray.push([ parseDate(elem.date), elem.nav ]);
		    });
		    self._chartData = dataArray.concat(self._chartData);
		}

		if(firstDate < toDate) {
		    self._fetchData(firstDate + 86400000, toDate, callback);
		} else {
		    callback();
		    self._updatingChart = false;
		}
	    }
	);
    },

    _bindEvents: function()
    {
	var self = this;
	this._chartElem
	    // Upon first hovering into the chart
	    .hover(
		function() { self._legendElem.fadeIn(250); },
		function() { self._legendElem.hide(); }
	    )
	    // Hovering in the chart area
	    .bind("plothover", function(event, pos, item) {
		self._latestPosition = pos;
		// Do not update the legend immediately, let the crosshair
		// plugin does its work first
		if(! self._updateLegendTimeout) {
		    self._updateLegendTimeout = setTimeout(
			function() { self._updateLegend(); }, 50);
		}
	    });

	this._overviewElem
	    .bind("plotselected", function (event, ranges) {
		self._overviewPlotSelected_evt(event, ranges);
	    });
    },

    _overviewPlotSelected_evt: function (event, ranges)
    {
	currentRange = ranges;
	if(
	    this._updatingChart ||
	    (
		currentRange.xaxis.from <= this._overviewStartDate &&
		currentRange.xaxis.to <= this._overviewStartDate
	    )
	)
	{
	    if(this._previousSelection != null) {
		this._overview.setSelection(this._previousSelection, true);
	    } else {
		this._overview.clearSelection(true);
	    }
	    return;
	}

	if(currentRange.xaxis.from < this._overviewStartDate) {
	    currentRange.xaxis.from = this._overviewStartDate;
	    this._overview.setSelection(currentRange, true);
	} 

	this._updatingChart = true;
	this._previousSelection = currentRange;
	this._showOverlay();

	var self = this;
	this._chartData = [];
	this._fetchData(
	    currentRange.xaxis.from, currentRange.xaxis.to,
	    function() {
		self.plotChart(self._chartData);
		self._hideOverlay();
	    });
    },

    _createLoadingOverlay: function()
    {
	var offset = this._chartElem.offset();
	this._overlay = $('<div class="overlay"></div>')
	    .css({
		background: '#fff url(/img/ajax-loader.gif) no-repeat center center',
//                background: '#fff url(/~felix/PBTracker/img/ajax-loader.gif) no-repeat center center',
		'height': this._chartElem.height(),
		left: offset.left,
		position: 'absolute',
		top: offset.top,
		'width': this._chartElem.width(),
		zIndex: 9999
	    });
	$('body').append(this._overlay);
	this._hideOverlay();
    },

    _showOverlay: function() { this._overlay.show().fadeTo(250, 0.65); },

    _hideOverlay: function() { this._overlay.css('opacity', 0).hide(); }
});

// MAIN LINE - load once all DOM elements are ready
$(function() {
    var priceChart = new PriceChart($('#price-chart'), $('#price-overview'));
    priceChart.plotChart(chartData);
    priceChart.plotOverview(overviewData);
});
