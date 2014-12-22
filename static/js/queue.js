var setupList = function() {
    var list = $("#slippylist")[0];
    list.addEventListener('slip:beforereorder', function(e){
        if (/demo-no-reorder/.test(e.target.className)) {
            e.preventDefault();
        }
    }, false);

    list.addEventListener('slip:beforeswipe', function(e){
        if (e.target.nodeName == 'INPUT' || /demo-no-swipe/.test(e.target.className)) {
            e.preventDefault();
        }
    }, false);

    list.addEventListener('slip:beforewait', function(e){
        if (e.target.className.indexOf('instant') > -1) e.preventDefault();
    }, false);

    list.addEventListener('slip:afterswipe', function(e){
        $(e.target).remove();
    }, false);

    list.addEventListener('slip:reorder', function(e){
        e.target.parentNode.insertBefore(e.target, e.detail.insertBefore);
        return false;
    }, false);
    new Slip(list);
};

var updatePlaylist = function() {
    $.getJSON('/api/player/queue', function(data) {
        var list = $("#slippylist");
        $.each(data['queue']['tracks'], function(i, e) {
            list.append("<li>"+e+"</li>");
        });
    });
};

$(document).ready(function(){
    setupList();
    updatePlaylist();
});
