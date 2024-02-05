// get current time, hours, minutes
var d = new Date();
var xhttpva = new XMLHttpRequest();

function runVideoAnalytics() {

    xhttpva.open("POST", "/video_events", true);
    xhttpva.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    var formData ="video_analytics_start=true"

    xhttpva.send(formData);
    postMessage(d.toLocaleTimeString() + ": Video analaytics initiatied.");

    xhttpva.onload = function() {
      try {
        // load new info
        const info = this.response;
        postMessage(d.toLocaleTimeString() + ": " + info);
      }
      catch(err) {
        postMessage(d.toLocaleTimeString() + ": " + err);
      }
    }

}

runVideoAnalytics();