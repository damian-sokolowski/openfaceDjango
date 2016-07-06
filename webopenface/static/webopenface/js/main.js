navigator.getUserMedia = navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia ||
    navigator.msGetUserMedia;

$.fn.exists = function(){return this.length != 0}

var defaultPerson = null;
var vid = document.getElementById('videoel'),
    vidReady = false;
var people = {}, defaultPerson = -1;

function sendFrameLoop() {
	console.log("loop");
    if (vidReady) {
        var canvas = document.createElement('canvas');
        canvas.width = vid.width;
        canvas.height = vid.height;
        var cc = canvas.getContext('2d');
        cc.drawImage(vid, 0, 0, vid.width, vid.height);
        var dataURL = canvas.toDataURL('image/jpeg', 0.6)
        $.ajax({
            url: "/openface/api/onmessage/",
            type : "POST",
            contentType: "application/json; charset=utf-8",
            dataType: 'json',
            data: JSON.stringify({
                type: 'FRAME',
                dataURL: dataURL,
                training: $("#trainingChk").prop('checked'),
                identity: defaultPerson,
            }),

            success: function (json) {
				console.log("ajax");
				if (typeof personSite !== 'undefined' && !$("#trainingChk").prop('checked')) {
					return;
				}
                console.log(json["ANNOTATED"]);
                if(json['ANNOTATED']){
                    $("#detectedFaces").html(
                        "<img src='" + json['ANNOTATED']['content'] + "' width='430px'>"
                    )
                } else if (json['NEW_IMAGE']) {

                } else if (json['IDENTITIES']) {

                }
                getPeopleInfoHtml()
				sendFrameLoop();
            },

            error: function (xhr, errmsg, err) {
                console.log('error FRAME');
                sendFrameLoop();
            }
        });
    }
}

function getPeopleInfoHtml() {
    var info = {'-1': 0};
    for (var key in people) {
        info[key] = 0;
    }
    //var len = images.length;
    //for (var i = 0; i < len; i++) {
    //    id = images[i].identity;
    //    info[id] += 1;
    //}
    if (typeof personSite != 'undefined') {
        var valueMax = $('#progress_bar div').attr('aria-valuemax')
        $('#progress_bar div').width((info[defaultPerson]/valueMax*100)+'%');
        $('#progress_bar span').text(info[defaultPerson]+'/'+valueMax);
        if (info[defaultPerson] >= valueMax) {
            $("#trainingChk").bootstrapToggle('off');
            $('#addPersonTxt').prop('readonly', false).val("");
            $('#addPersonBtn').prop('disabled', false);
        }
        var h = "";
    } else {
        var h = "<li><b>Unknown:</b> "+info['-1']+"</li>";
    }
    for (var key in people) {
        h += "<li><b>"+people[key]+":</b> "+info[key]+"</li>";
    }

    $("#peopleInfo").html(h);
}

function camSuccess(stream){
    vid.src = (window.URL.createObjectURL(stream)) || stream;
    vid.play();
    vidReady = true;
    sendFrameLoop();
}

function trainingChkCallback() {
    sendFrameLoop();
    //$.ajax({
    //    url : "/openface/api/onmessage/",
    //    type : "POST",
    //    data : {
		//	type: 'TRAINING',
		//	val: $("#trainingChk").prop('checked')
		//},
    //
    //    success : function(json) {
    //        console.log('trai');
    //        console.log($("#trainingChk").prop('checked'));
		//	sendFrameLoop();
    //    },
    //
    //    error : function(xhr,errmsg,err) {
		//	console.log('error training');
    //    }
    //});
}

function addPerson(){
    console.log('click');
    var newPerson = $("#addPersonTxt").val();
    if (newPerson != '') {
        $('#addPersonTxt').prop('readonly', true);
        $('#addPersonBtn').prop('disabled', true);
        $.ajax({
            url: "/openface/api/onmessage/",
            type: "POST",
            contentType: "application/json; charset=utf-8",
            dataType: 'json',
            data: JSON.stringify({
                type: 'ADD_PERSON',
                val: newPerson
            }),

            success: function (json) {
                console.log('yea');
                defaultPerson = null;
                if (json.hasOwnProperty('id')) {
                    defaultPerson = json['id'];
                    people[defaultPerson] = newPerson;

                    if (typeof personSite !== 'undefined') {
	                    $("#trainingChk").bootstrapToggle('on');
                        trainingChkCallback()
                    }
                }
            },

            error: function (xhr, errmsg, err) {
                console.log('error add_person');
            }
        });
    }
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
    $("#trainingChk").change(trainingChkCallback);
});