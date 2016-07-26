navigator.getUserMedia = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia;

$.fn.exists = function(){return this.length != 0}

var defaultPerson = null;
var vid = document.getElementById('videoel'),
    vidReady = false;
var people = {}, defaultPerson = -1,
    images = [];

function sendFrameLoop() {
    if (vidReady) {
        var canvas = document.createElement('canvas');
        canvas.width = vid.width;
        canvas.height = vid.height;
        var cc = canvas.getContext('2d');
        cc.drawImage(vid, 0, 0, vid.width, vid.height);
        var dataURL = canvas.toDataURL('image/jpeg', 0.6);

    }
}

function camSuccess(stream){
    vid.src = (window.URL.createObjectURL(stream)) || stream;
    vid.play();
    vidReady = true;
    sendFrameLoop();
}

function addPerson(){
    var newPerson = $("#addPersonTxt").val();
}

$(document).ready(function(){
    if ( !$('#previewPage').exists()) {
        if (navigator.getUserMedia) {
            navigator.getUserMedia({video: true}, camSuccess,
                function () {
                    alert('Błąd przechwytywania obrazu z kamery');
                }
            )
        } else {
            alert('Nie wykryto kamery');
        }
    }

	$("#addPersonBtn").click(addPerson);
    //$("#trainingChk").change(trainingChkCallback);
});