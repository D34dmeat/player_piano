var queueTracks = {}; // track_id -> track details

var renderQueuePage = function() {
    $("#async_container").html("");
    updateQueuelist(function() {
        $("#queue_container").show();
    });
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
        queueTracks = {};
        $.each(data['queue'], function(i, track) {
            list.append(nunjucks.renderString("<li data-track-id='{{track_id}}'><table class='table'><tr><td class='track-icon'><img src='/static/img/equalizer.gif'/></td><td class='col-md-6'><a class='track asnyc'>{{title}}</a></td><td class='col-md-1'>{{length}}</td><td class='col-md-2'>{{artist}}</td><td class='col-md-4'>{{collection}}</td></tr></table></li>", {
                title: track.title,
                track_id: track.id,
                length: parseInt(track.length / 60) + ":" + ("00"+track.length % 60).slice(-"00".length),
                artist: track.collection.artist.name,
                collection: track.collection.name
            }));
            queueTracks[track.id] = track;
            $("#queuelist li[data-track-id="+track.id+"] a.track").click(function() {
                playQueueTrack(i);
            });
        });
        player_state_callback();
        if (callback) {
            callback();
        }
        $("#queue-clear").unbind("click").click(function() {
            requestPlayerState("clear_queue", updateQueuelist);
        });
    });
};

var playQueueTrack = function(track_num, callback) {
    $.ajax({
        type: "POST",
        url: '/api/player/play_queue_track',
        data: JSON.stringify({track_num:track_num}),
        contentType: 'application/json'
    }).success(function(data) {
        if (callback)
            callback();
    }).error(function(data) {
        console.log(data);
        alert("error: "+data.status+" "+data.statusText+" "+data.responseText);
    });
}

var player_state_callback = function() {
    $("#queuelist li").removeClass("current_track");
    if(playerState.queue) {
        $($("#queuelist li")[playerState.queue.current_track_num]).addClass("current_track");
        if(playerState.state == "playing" || playerState.state == "paused") {
            showPlayerTrackDetails();
        }
        if(playerState.state == "playing") {
            $("#player-play-button").removeClass("glyphicon-play").addClass("glyphicon-pause");
            $("#queuelist .track-icon").removeClass("playing");
            $($("#queuelist td.track-icon")[playerState.queue.current_track_num]).addClass("playing");
        } else {
            $("#queuelist .track-icon").removeClass("playing");
            $("#player-play-button").removeClass("glyphicon-pause").addClass("glyphicon-play");
            showPlayerTrackDetails(false);
        }
    }
}

var player_position_update_callback = function(e) {
    var percent_complete = ((playerState.track_pos.measure / playerState.track_length)*100).toFixed(2) + "%";
    $("#player-progress .progress-bar").css("width", percent_complete);
}

var load_track_callback = function() {
}

