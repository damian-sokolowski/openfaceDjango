var number_of_video_devices = 0;

function getFrameLoop() {
    $.ajax({
        url: "/openface/api/onmessage/",
        type : "POST",
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        data: JSON.stringify({
            type: 'GET_FRAME'
        }),

        success: function (json) {
            if (json['publishedRecently']) {
                var recognized = json["recognizedPeople"]['recognized_list'];
                var number_of_unknown = json["recognizedPeople"]['number_of_unknown'];
                var list = $("<ul></ul>");
                var detected_people = $('#detectedPeople div');
                $("#detectedFacesId").attr('src', json['dataURL']);
                if (recognized.length > 0 || number_of_unknown > 0) {
                    $.each(recognized, function(index, value){
                        list.append("<li>" + value + "</li>");
                    });
                    list.append("<li>Unknown: " + Math.round(number_of_unknown / number_of_video_devices) + "</li>");
                    detected_people.html(list);
                } else {
                    detected_people.html("<p>Nobody detected.</p>");
                }
            } else {
                $("#detectedFaces").html('');
                $('#detectedPeople div').html('<p>No camera.</p>')
            }
            getFrameLoop()
        },

        error: function (xhr, errmsg, err) {
            console.log('error GET_FRAME');
            getFrameLoop()
        }
    });
}

function errorLog(error) {
    console.log('navigator.getUserMedia error: ', error);
}

$('document').ready(function() {
    navigator.mediaDevices.enumerateDevices()
        .then(function(deviceInfos){
            deviceInfos.forEach(function(deviceInfo){
                if (deviceInfo.kind === 'videoinput') {
                    number_of_video_devices++;
                }
            });
        })
        .catch(errorLog);

    getFrameLoop();
})