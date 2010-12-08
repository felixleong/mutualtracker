function parseDate(s) {
    var parts = s.split("-");
    return Date.UTC(parts[0], parts[1]-1, parts[2]);
}

function toShortDate(ms) {
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    var d = new Date(ms);

    return d.getDate() + " " + months[d.getMonth()] + " " + d.getFullYear();
}

function toISO8601DateString(ms) {
    var d = new Date(ms);
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
}

function generateCakePhpUrlParameters(params) {
    var urlParam = '';
    $.each(params, function(key, value) {
	urlParam += '/' + key + ':' + value;
    });
    return urlParam;
}
