var midiEventListener = function() {
    var wsUri = "ws://" + window.location.host + "/api/player/events";
    ws = new WebSocket(wsUri);
    ws.onmessage = function(evt) {
        var data = JSON.parse(evt.data);
        
        if (data['type'] == 'load_track') {
            indicate_playing_track(data);
        }
        //console.log(data);
    }

};

