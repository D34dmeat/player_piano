var renderQueuePage = function() {
    $("#async_container").html("");
    $("#queue_container").show();
};

var cleanupQueuePage = function() {
    $("#queue_container").hide();    
};

var setupQueueList = function() {
    var list = $("#queuelist")[0];
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

var updateQueuelist = function(callback) {
    $.getJSON('/api/player/queue', function(data) {
        var list = $("#queuelist");
        $("#queuelist li").remove();
        console.log(data);
        $.each(data['queue'], function(i, track) {
            list.append(nunjucks.renderString("<li data-track-id='{{track_id}}'><table class='table'><tr><td class='track-icon'><img src='/static/img/equalizer.gif'/></td><td class='col-md-6'>{{title}}</td><td class='col-md-1'>{{length}}</td><td>{{artist}}</td><td>{{collection}}</td></tr></table></li>", {
                title: track.title,
                track_id: track.id,
                length: track.length,
                artist: track.collection.artist.name,
                collection: track.collection.name
            }));
        });
        if (callback) {
            callback();
        }
    });
};

var indicate_playing_track = function(e) {
    $("#queuelist .track-icon").removeClass("playing");
    updateQueuelist(function(){
        $($("#queuelist td.track-icon")[e.current_track_num]).addClass("playing");
    });    
}

