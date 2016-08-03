function getFrameLoop() {
    console.log('img');
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
                    var list = $("<ul></ul>");
                    $("#detectedFaces").html(
                        "<img src='" + json['dataURL'] + "' width='430px'>"
                    );
                    $.each(json['detectedPeople'], function(index, value){
                        list.append('<li>'+value[0]+' - '+value[1]+'</li>')
                    });
                    $('#detectedPeople div').html(list)

                } else {
                    $("#detectedFaces").html('');
                    $('#detectedPeople div').html('<p>No camera.</p>')
                }
                getFrameLoop()
            },

            error: function (xhr, errmsg, err) {
                console.log('error GET_FRAME');
            }
        });
}

$('document').ready(function() {
    getFrameLoop();
})