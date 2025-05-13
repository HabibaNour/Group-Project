//Code is adpated from the following sources:
//https://www.w3schools.com/js/
//https://socket.io/docs/v3/emitting-events/
//https://medium.com/cstech/javascript-understanding-customevent-and-dispatchevent-a33d10075818
//https://stackoverflow.com/questions/6193574/save-javascript-objects-in-sessionstorage

var socket = io.connect("http://localhost:5000");

let all_devices = JSON.parse(sessionStorage.getItem("devices")) || {};
let alerts = JSON.parse(sessionStorage.getItem("alerts")) || {};

socket.on("new_mac", function (data) {
    if (!all_devices[data.mac]) {
        all_devices[data.mac] = data;
        sessionStorage.setItem("devices", JSON.stringify(all_devices));

        var alert_data = {mac: data.mac, timestamp: data.timestamp || new Date().toLocaleString()};
        alerts[Date.now()] = alert_data;
        sessionStorage.setItem("alerts", JSON.stringify(alerts));

        //event = name of event, information to be sent
        var event = new CustomEvent("device_connected", { detail: data });
        window.dispatchEvent(event);
    }
});
