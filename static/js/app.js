var page_handlers = {
    "/"       : renderQueuePage,
    "/library": renderLibraryPage,
    "/queue"  : renderQueuePage
};

var renderPage = function(path) {
    var page_handler = page_handlers['/'+path.split('/')[1]];
    if (page_handler == undefined || path[0] != '/') {
        alert("No page handler for '"+path);
    } else {
        // Push the new page state on to the history, as long as we are
        // not already on that page 
        if (path != location.pathname) {
            history.pushState({
            }, null, path);
        }
        //Render the page:
        $("#async_container").html("");
        page_handler();
    }
}

var getModelJSON = function() {
    var model = arguments[0];
    var query;
    var callback;
    if (typeof arguments[1] == "function") {
        callback = arguments[1];
    } else {
        query = arguments[1];
        callback = arguments[2];
    }
    var path = "/api/"+model;
    if (typeof query == "object") {
        path = "/api/"+model+"?q="+JSON.stringify(query);
    } else if (typeof query == "number") {
        path = "/api/"+model+"/"+query;
    } 
    $.getJSON(path, function(data) {
        if(typeof query != "number") {
            data = data['objects'];
        }
        console.log(data);
        callback(data);
    });
};

var renderTemplate = function(template, data) {
    var html = nunjucks.render(template, data);
    $("#async_container").append(html);
    //Turn links into async links:
    $('#async_container a.async').unbind("click").click(function(e) {
        //Disable regular link behaviour:
        e.preventDefault();
        renderPage($(e.target).attr('href'));
    });
};


var setupAsyncPageNavigation = function() {
    window.addEventListener("popstate", function(e) {
        renderPage(location.pathname);
    });
    renderPage(location.pathname);
    //Turn links into async links:
    $('a.async').unbind("click").click(function(e) {
        //Disable regular link behaviour:
        e.preventDefault();
        renderPage($(e.target).attr('href'));
    });
};

$(document).ready(function() {

    nunjucks.configure("/static/client_templates", {
        autoescape: true
    });
    
    setupAsyncPageNavigation();
});
