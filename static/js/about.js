var aboutModalPopstate = function() {
    //Hide the about modal dialog when we pop back to an earlier state:
    $("#aboutModal").modal('hide');
}

var renderAboutPage = function() {
    $("#aboutModal").modal('show');
    return {popstate_callback: "aboutModalPopstate"}
}

$(document).ready(function() {
    $("#aboutModal .dismiss").click(function(e) {
        window.history.go(-1);
    });
});
