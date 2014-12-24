// string formatting helper:
if (!String.prototype.format) {
    String.prototype.format = function() {
        var args = arguments;
        this.unkeyed_index = 0;
        return this.replace(/\{(\w*)\}/g, function(match, key) { 
            if (key === '') {
                key = this.unkeyed_index;
                this.unkeyed_index++
            }
            if (key == +key) {
                return args[key] !== 'undefined'
                    ? args[key]
                    : match;
            } else {
                for (var i = 0; i < args.length; i++) {
                    if (typeof args[i] === 'object' && typeof args[i][key] !== 'undefined') {
                        return args[i][key];
                    }
                }
                return match;
            }
        }.bind(this));
    };
}


function exponentialBackoff (k, limit) {
    var maxInterval = (Math.pow(2, k) - 1) * 1000;
    
    if (limit === undefined) {
        limit = 30;
    }
    if (maxInterval > limit*1000) {
        maxInterval = limit*1000; // If the generated interval is more than [limit] seconds, truncate it down to [limit] seconds.
    }
    
    return maxInterval; 
}
