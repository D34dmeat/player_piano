var setupPlayLinks = function() {
    $("table.tracklist").each(function(i, table) {
        var tracks_type = $(table).data('tracks-type')
        $("a.track").each(function(i, link) {
            var link = $(link);
            var request = {};
            if (tracks_type == 'collection') {
                request['type'] = 'collection';
                request['id'] = link.data('collection');
            } else if (tracks_type == 'playlist') {
                request['type'] = 'playlist';
                request['id'] = link.data('playlist');
            }            
            request['track_num'] = i;

            $(link).click(function(e) {
                //Clear the queue, enqueue the entire collection, skipping
                //to the track clicked on:
                $.ajax({
                    type: "POST",
                    url: '/api/player/play',
                    data: JSON.stringify(request),
                    contentType: 'application/json'
                }).success(function(data) {
                    alert(JSON.stringify(data));
                }).error(function(data) {
                    console.log(data);
                    alert("error: "+data.status+" "+data.statusText+" "+data.responseText);
                });                
                e.preventDefault();
            });
        });
    });
}

$(document).ready(function() {
    setupPlayLinks();
});
