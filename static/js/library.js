var renderLibraryPage = function(path) {

    // @app.route('/library')
    // @app.route('/library/folder/<int:folder_id>/<name>')
    // @app.route('/library/folder/<int:folder_id>/artist/<int:artist_id>/<name>')
    // @app.route('/library/folder/<int:folder_id>/collection/<int:collection_id>/<name>')
    var folder_id;
    var artist_id;
    var collection_id;
    var links = [];

    var root_match = path.match("^/library/?$");
    var folder_match = path.match("^/library/folder/([0-9]+)/([^/]+)$");
    var artist_match = path.match("^/library/artist/([0-9]+)/([^/]+)$");
    var collection_match = path.match("^/library/collection/([0-9]+)/([^/]+)$");

    if (root_match) {
        //get all folders:
        getModelJSON('folder', function(folders) {
            $.each(folders, function(i, folder) {
                links.push({type:'folder', name:folder.name, href:'/library/folder/{}/{}'.format(folder.id,  folder.name)})
            });
            renderTemplate('library.html', {title:'Library', links:links});
        });
    } else if (folder_match) {
        folder_id = parseInt(folder_match[1]);
        //get all artists in folder:
        getModelJSON('folder', folder_id, function(folder) {
            getModelJSON('artist', {filters:[{name:'folder_id', op:'eq', val:folder_id}],
                                    order_by:[{field:'name'}]}, function(artists) {
                var title = '<a class="async" href="/library">Library</a> / {folder_name}'.format({
                    folder_id: folder.id,
                    folder_name: folder.name
                });
                $.each(artists, function(i, artist) {
                    links.push({type:'artist', name:artist.name, href:'/library/artist/{}/{}'.format(artist.id,  artist.name)})
                });
                renderTemplate('library.html', {title:title, links:links});
            });
        });
    } else if (artist_match) {
        artist_id = parseInt(artist_match[1]);
        //get all collections for artist:
        getModelJSON('artist', artist_id, function(artist) {
            getModelJSON('collection', {filters:[{name:'artist_id', op:'eq', val:artist_id}],
                                        order_by:[{field:'name'}]}, function(collections) {
                var title = '<a class="async" href="/library">Library</a> / <a class="async" href="/library/folder/{folder_id}/{folder_name}">{folder_name}</a> / {artist_name}'.format({
                    folder_id: artist.folder.id,
                    folder_name: artist.folder.name,
                    artist_id: artist.id,
                    artist_name: artist.name
                });
                $.each(collections, function(i, collection) {
                    links.push({type:'collection',name:collection.name,href:'/library/collection/{}/{}'.format(collection.id, collection.name)})
                });
                renderTemplate('library.html', {title:title, links:links});                
            });
        });
    } else if (collection_match) {
        //get collection
        collection_id = parseInt(collection_match[1]);
        getModelJSON('collection', collection_id, function(collection) {
            getModelJSON('folder', collection.artist.folder_id, function(folder) {
                var title = '<a class="async" href="/library">Library</a> / <a class="async" href="/library/folder/{folder_id}/{folder_name}">{folder_name}</a> / <a class="async" href="/library/artist/{artist_id}/{artist_name}">{artist_name}</a> / {collection_name}'.format({
                    folder_id: folder.id,
                    folder_name: folder.name,
                    artist_id: collection.artist.id,
                    artist_name: collection.artist.name,
                    collection_name: collection.name
                });
                var show_tempo = false;
                $.each(collection.tracks, function(i, track) {
                    if (track.human_tempo)
                        show_tempo = true;
                    links.push({type:'track', 
                                name:track.title, 
                                track_id:track.id, 
                                length:parseInt(track.length / 60) + ":" + ("00"+track.length % 60).slice(-"00".length), 
                                tempo: track.human_tempo,
                                collection:collection_id, 
                                collection_order:track.collection_order});
                });
                renderTemplate('library.html', {title:title, links:links, show_tracks:true, show_tempo:show_tempo, tracks_type:"collection"});
                setupPlayLinks();
            });
        });
    }
};

var setupPlayLinks = function() {
    $("table.tracklist").each(function(i, table) {
        var tracks_type = $(table).data('tracks-type')
        $(".tracklist a.track").each(function(i, link) {
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
                    renderPage('/queue');
                }).error(function(data) {
                    console.log(data);
                    alert("error: "+data.status+" "+data.statusText+" "+data.responseText);
                });
                e.preventDefault();
            });
        });
        $(".tracklist .play-button").each(function(i, button) {
            $(button).click(function(e) {
                $(button).siblings("a.track").click();
            });
        });
    });
}

