/*chrome.runtime.onInstalled.addListener(() => {
    const ws = new WebSocket("ws://127.0.0.1:8765/");
    //var url = window.location.href;
    console.log(ws);
    ws.onopen = function(event){
        send();
    };
    ws.onmessage = function(event){
        console.log("EV" + event)
    };
    function send(){
        ws.send("hola")
        //ws.send(url)
    }

});*/
var url = ""
chrome.tabs.query({active: true, lastFocusedWindow: true}, tabs => {
    url = tabs[0].url;
    // use `url` here inside the callback because it's asynchronous!
});

//function download() {
const ws = new WebSocket("ws://127.0.0.1:8765/");

console.log(ws);
ws.onopen = function(event){
    setTimeout(send, 50);
};
ws.onmessage = function(event){
    data = event.data
    if (data == "confirmed") {
        document.getElementById("state").innerHTML = "Downloading now"
        ws.send("confirmed")
    }
    if (data == "finished_0") {
        document.getElementById("state").innerHTML = "Finished correctly"
    }
    if (data == "finished_1") {
        document.getElementById("state").innerHTML = "Some error has ocurred"
    }
};
function send(){
    if (url.indexOf("https://www.youtube.com/watch?v=") == 0)
        ws.send(url)
    else
        alert("That's not a youtube video url")
    //ws.send(url)
}
//}

/*
"background": {
        "service_worker": "background.js"
    },
    */
