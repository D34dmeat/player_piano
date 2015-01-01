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
    var valid_states = ['play','stop','pause','next_track','prev_track','restart_track'];
    if (valid_states.indexOf(state) < 0) {
        alert("Invalid play state: " + state);
    }
    player_service(state).then(
        function(result) {
            if (callback)
                callback();
        },
        function(error) {
            console.log(error);
            alert(error.error);            
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

var midiEventListener = function(session) {
    
    var load_track = function(data) {
        $.each(data, function(i, event) {
            playerState.track_length = event['track_length'];
            playerState.queue = event['queue'];
            playerState.track_id = event['track_id'];
            load_track_callback();
        });
    }
    var player_state = function(data) {
        $.each(data, function(i, event) {
            playerState.state = event.state;
            setupPlayerButtons();
            player_state_callback();
        });
    }
    var position_update = function(data) {
        $.each(data, function(i, event) {
            playerState.track_pos = event['pos'];
            player_position_update_callback();
        });
    }

    var start = function(callback) {
        //Play state and load track events may have happened before we
        //started listening, so update those manually first:
        console.log("midi event listener startup...")
        midi_service('get_player_state').then(function(result){
            load_track([result]);
            player_state([{state: result.play_state}]);

            //Start listening to realtime events:
            session.subscribe('player_piano.midi.event.load_track', load_track);
            session.subscribe('player_piano.midi.event.player_state', player_state);
            session.subscribe('player_piano.midi.event.position_update', position_update);
            callback();
        });
    }

    return {
        start : start
    }
};

