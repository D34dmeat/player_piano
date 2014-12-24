var playerState;
var resetPlayerState = function() {
    playerState =  {
        state : "initialized",
        track_id: null,
        track_length: null,
        track_pos: null,
        queue: null
    }
};
resetPlayerState();

var requestPlayerState = function(state, callback) {
    $.ajax({
        type: "POST",
        url: '/api/player/'+state,
        data: "{}",
        contentType: 'application/json'
    }).success(function(data) {
        if (callback)
            callback();
    }).error(function(data) {
        console.log(data);
        alert("error: "+data.status+" "+data.statusText+" "+data.responseText);
    });
}

var setupPlayerButtons = function() {
    $("#player .player-button").unbind('click').removeClass("player-disabled");
    
    var ensureOneClick = function() {
        $("#player .player-button").unbind('click').addClass("player-disabled");
    }

    $("#player-play-button").click(function() {
        ensureOneClick();
        if (playerState.state != "playing") {
            requestPlayerState("play");
        } else {
            requestPlayerState("pause");
        }
    });
    $("#player-next-track-button").click(function() {
        ensureOneClick();
        requestPlayerState("next_track");
    });
    $("#player-prev-track-button").click(function() {
        ensureOneClick();
        //If we're within the first two measures, go to the previous track:
        if (playerState.track_pos.measure <= 2) {
            requestPlayerState("prev_track");
        } else {
        //Otherwise, go to the beginning of the track:
            requestPlayerState("restart_track");
        }
    });

}

var showPlayerTrackDetails = function(on_off) {
    if (on_off == undefined || on_off == true){
        $("#player-left").addClass("playing");
        if (playerState.track_id) {
            var track = queueTracks[playerState.track_id];
            if (track) {
                $("#player-track-title").text(track.title);
                $("#player-artist-title").text(track.collection.artist.name);
                $("#player-collection-title").text(track.collection.name);
            } else {
                $("#player-left").removeClass("playing");
            }
        }
    } else {
        $("#player-left").removeClass("playing");
        $("#player-progress .progress-bar").css("width", "0%");
    }
}

var midiEventListener = function(connectionAttempts) {
    var wsUri = "ws://" + window.location.host + "/api/player/events";
    var ws = new WebSocket(wsUri);
    if (connectionAttempts == undefined) {
        connectionAttempts = 0;
    }
    ws.onmessage = function(evt) {
        connectionAttempts = 0;
        var data = JSON.parse(evt.data);
        if (data['type'] == 'load_track') {
            playerState.track_length = data['track_length'];
            playerState.queue = data['queue'];
            playerState.track_id = data['track_id'];
            console.log(data);
            load_track_callback();
        }
        else if (data['type'] == 'player_state') {
            playerState.state = data.state;
            setupPlayerButtons();
            player_state_callback();
        }
        else if (data['type'] == 'position_update') {
            playerState.track_pos = data['pos'];
            player_position_update_callback();
        }
    };
    ws.onclose = function(evt) {
        resetPlayerState();
        var timeToWait = exponentialBackoff(connectionAttempts, 10);
        setTimeout(function() {
            console.log("Attempting to reconnect to player events websocket in {} seconds..".format(timeToWait / 1000));
            midiEventSocket = midiEventListener(connectionAttempts+1);
        }, timeToWait);
    };
    return ws;

};

