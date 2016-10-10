$.fn.exists = function(){return this.length != 0};

var people = {}, defaultPerson = -1,
    images = [];
var videoSourcesList = [];
var vidReady = false, startedFrameLoop = false;
var vidWidth, vidHeight;

function sendFrameLoop() {
    var training = $("#trainingChk").prop('checked');
    if ($('#personPage').exists() && !training) {
        return;
    }
    if (vidReady) {
        startedFrameLoop = true;
        var videoels = document.getElementById('tab-preview').getElementsByTagName('video');
        var canvas = document.createElement('canvas');
        canvas.width = vidWidth;
        canvas.height = vidHeight*videoels.length;
        var cc = canvas.getContext('2d');
        for (var i = 0; i < videoels.length; i++){
            var vid = videoels[i];
            cc.drawImage(vid, 0, vid.height*(i), vid.width, vid.height);
        }
        var dataURL = canvas.toDataURL('image/jpeg');

        $.ajax({
            url: "/openface/api/onmessage/",
            type : "POST",
            contentType: "application/json; charset=utf-8",
            dataType: 'json',
            data: JSON.stringify({
                type: 'FRAME',
                dataURL:dataURL,
                training: training,
                identity: defaultPerson
            }),

            success: function (json) {
                if(json['ANNOTATED']){
                    $("#detectedFacesId").attr('src', json['ANNOTATED']['content']);
                }

                if (json['NEW_IMAGE']) {
                    var j = json['NEW_IMAGE'];
                    images.push({
                        hash: j.hash,
                        identity: j.identity,
                        image: j.content,//getDataURLFromRGB(j.content),
                        representation: j.representation
                    });
                    $("#detectedFaces").html(
                        "<img src='" + j.content + "' width='430px'>"
                    )
                }

                // if (json['IDENTITIES']) {
                //     var identities = json["IDENTITIES"]['identities'];
                //     var list = $("<ul></ul>");
                //     var detected_people = $('#detectedPeople div');
                //     detected_people.html("Last updated: " + (new Date()).toTimeString());
                //     if (identities.length > 0) {
                //         $.each(identities, function(index, value){
                //             list.append("<li>"+value+"</li>")
                //         });
                //         detected_people.append(list)
                //     } else {
                //         detected_people.append("<p>Nobody detected.</p>");
                //     }
                // }
                if (json['RECOGNIZED']) {
                    var recognized = json["RECOGNIZED"]['recognized_list'];
                    var number_of_unknown = json["RECOGNIZED"]['number_of_unknown'];
                    var list = $("<ul></ul>");
                    var detected_people = $('#detectedPeople div');
                    detected_people.html("Last updated: " + (new Date()).toTimeString());
                    if (recognized.length > 0 || number_of_unknown > 0) {
                        $.each(recognized, function(index, value){
                            list.append("<li>" + value + "</li>");
                        });
                        list.append("<li>Unknown: " + Math.round(number_of_unknown / videoels.length) + "</li>");
                        detected_people.append(list);
                    } else {
                        detected_people.append("<p>Nobody detected.</p>");
                    }
                }
                getPeopleInfoHtml();
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
    var training = $("#trainingChk").prop('checked');
    if (training){
        var info = {'-1': 0};
        $.each(people, function(index, value) {
            info[index] = 0;
        });
        var len = images.length;
        for (var i = 0; i < len; i++) {
            info[images[i].identity] += 1;
        }

        var valueMax = $('#progress_bar div').attr('aria-valuemax');
        $('#progress_bar div').width((info[defaultPerson]/valueMax*100)+'%');
        $('#progress_bar span').text(info[defaultPerson]+'/'+valueMax);

        var list = $("<ul></ul>");
        $.each(people, function(index, value){
            list.append("<li><b>"+people[index]+":</b> "+info[index]+"</li>")
        });
        $('#peopleInfo').html(list);

        if (info[defaultPerson] >= valueMax && training) {
            $("#trainingChk").bootstrapToggle('off');
            $('#addPersonTxt').prop('readonly', false).val("");
            $('#addPersonBtn').prop('disabled', false);
            $('#progress_bar div').width('0%');
            $('#progress_bar span').text('0/'+valueMax);
            $.ajax({
                url: "/openface/api/onmessage/",
                type : "POST",
                contentType: "application/json; charset=utf-8",
                dataType: 'json',
                data: JSON.stringify({type: 'TRAIN_SVM'}),
                success: function (json) {
                    console.log('TRAIN_SVM');
                },
                error: function (json) {
                }
            });
        }
    }
}

function addPerson(){
    var newPerson = $("#addPersonTxt").val();
    if (newPerson != '') {
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
                defaultPerson = null;
                if (json.hasOwnProperty('id')) {
                    $('#addPersonTxt').prop('readonly', true);
                    $('#addPersonBtn').prop('disabled', true);
                    $("#trainingChk").bootstrapToggle('on');
                    defaultPerson = json['id'];
                    people[defaultPerson] = newPerson;

                    if ($('#personPage').exists()) {
                        sendFrameLoop();
                    }
                }
            },

            error: function (xhr, errmsg, err) {
                console.log('error add_person');
            }
        });
    }
}

function camSuccess(stream) {
    var videoElement = document.createElement('video');
    videoElement.width = vidWidth;
    videoElement.height = vidHeight;
    videoElement.src = (window.URL.createObjectURL(stream)) || stream;
    videoElement.play();
    document.querySelector('#tab-preview').appendChild(videoElement);
    vidReady = true;
    if (!startedFrameLoop) {
        sendFrameLoop();
    }
}

function start() {
    videoSourcesList.forEach(function(videoSource) {
        var constraints = {
            video: {deviceId: videoSource ? {exact: videoSource} : undefined}
        };
        navigator.mediaDevices.getUserMedia(constraints)
            .then(camSuccess)
            .catch(errorLog);
    });
}

function gotDevices(deviceInfos) {
    deviceInfos.forEach(function(deviceInfo){
        if (deviceInfo.kind === 'videoinput') {
            videoSourcesList.push(deviceInfo.deviceId);
        }
    });
    start();
}

function errorLog(error) {
    console.log('navigator.getUserMedia error: ', error);
}

$(document).ready(function(){
    if ( $('#mainPage').exists()) {
        vidWidth = 800;
        vidHeight = 600;
    } else {
        vidWidth = 400;
        vidHeight = 300;
    }

    navigator.mediaDevices.enumerateDevices()
        .then(gotDevices)
        .catch(errorLog);

	$("#addPersonBtn").click(addPerson);
});