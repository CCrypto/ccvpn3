var NPINGS = 6;
var TIMEOUT = 3000;

function img_ping(host, callback, avg, count) {
    var start;

    var avg = avg || 0;
    if (typeof(count) === 'undefined') {
        // -1 to ignore the first ping, so the DNS lookup does not change
        // the average time.
        count = -1;
        callback('...');
    }
    count = count + 1;


    if (count > 0) {
        // no timeout for the first ping, DNS can be slow
        var timer = setTimeout(function() {
            callback('timeout');
        }, TIMEOUT);
    }

    function ok() {
        var time = new Date() - start;

        clearTimeout(timer);

        if (count > 0) {
            avg = ((avg * (count-1)) + time) / (count);
        } else {
            avg = 0;
        }

        if (count >= NPINGS) {
            callback(Math.round(avg) + 'ms');
        } else {
            ping(host, callback, avg, count);
        }
    }


    var img = new Image();
    img.onload = ok;
    img.onerror = ok;

    start = new Date();
    img.src = 'http://' + host + '/ping';

    callback('...');
}

function perf_ping(host, callback, start) {
    if (start == undefined) {
        var perfEntries = performance.getEntries();
        // use the last perf entry to ignore any request preceding
        // this ping() call
        start = 0;
        for (var i = 0; i < perfEntries.length; i++) {
            if (start < perfEntries[i].startTime) {
                start = perfEntries[i].startTime;
            }
        }
        console.log("start: " + start);
    }

    var timer = setTimeout(function() {
        callback('timeout');
    }, TIMEOUT);

    var url = 'http://' + host + '/ping';
    var random_thing = "?" + String(Math.random()).slice(2)

    function ok() {
        clearTimeout(timer);

        var average = 0;
        var count = 0;

        var perfEntries = performance.getEntries();
        for (var i = 0; i < perfEntries.length; i++) {
            var e = perfEntries[i];

            // ignore old entries
            if (e.startTime < start) {
                continue;
            }

            // ignore other stuff
            if (e.name.slice(0, url.length) != url || e.entryType != 'resource') {
                continue;
            }

            var time = e.duration - Math.max(e.requestStart - e.startTime, 0);
            average = (average*count + time) / (count+1);
            count += 1;
        }

        if (count < NPINGS) {
            ping(host, callback, count, start);
            return;
        }

        average -= 2; // average difference to a simple icmp ping
        callback(Math.round(average) + 'ms');
    }

    var img = new Image();
    img.onload = ok;
    img.onerror = ok;
    img.src = url + random_thing;
    callback('...');
}

var ping = (performance) ? perf_ping : img_ping;

window.addEventListener('load', function() {
    var lines = document.getElementsByClassName('host_line');
    for (var i=0; i<lines.length; i++) {
        var line = lines[i];
        
        var ping_link = document.createElement('a');
        ping_link.href = '#';
        ping_link.innerHTML = '[ping]';
        ping_link.onclick = (function(line) {
            return function() {
                var host = line.children[0].innerHTML;
                console.log("ping: " + host);
                result = ping(host,
                    function(r) {
                        line.children[1].innerHTML = '[ping:&nbsp;'+r+']';
                    });
                return false;
            }
        })(line);
        line.appendChild(ping_link);
    }
}, false);

