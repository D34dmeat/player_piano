var page_handlers = {
    "/"       : renderQueuePage,
    "/library": renderLibraryPage,
    "/queue"  : renderQueuePage,
    "/about"  : renderAboutPage
};

var cleanup_handlers = {
    "/queue"  : cleanupQueuePage
};



var renderPage = function(path) {
    var page_handler = page_handlers['/'+path.split('/')[1]];
    if (page_handler == undefined || path[0] != '/') {
        console.log("No page handler for '"+path+"'");
    } else {
        //Cleanup the current page
        var cleanup_handler = cleanup_handlers['/'+location.pathname.split('/')[1]];
        if (cleanup_handler) {
            cleanup_handler();
        }
        //Render the page. Page handler returns the state to return to
        //if we come back to the current page.
        var state = page_handler(path);
        history.replaceState($.extend({}, history.state, state));
        // Push the new page state on to the history, as long as we are
        // not already on that page 
        if (path != location.pathname) {
            history.pushState(null, null, path);
        }
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

var renderTemplate = function(template, data, clear) {
    if (clear != false) {
        $("#async_container").html("");
    }
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
        if (e.state && e.state['popstate_callback']) {
            eval(e.state['popstate_callback'])();
        }
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

    //Render the queue once, but make it invisible when we're not on
    //the queue page.
    var queue_html = nunjucks.render('queue.html');
    $("#queue_container").append(queue_html).hide();
    setupQueueList();

    setupAsyncPageNavigation();

    midiEventListener();
});
