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

        var event = new CustomEvent("device_connected", { detail: data });
        window.dispatchEvent(event);
    }
});
