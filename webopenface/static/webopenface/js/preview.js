function getFrameLoop() {
    console.log('img');
    $.ajax({
            url: "/openface/api/onmessage/",
            type : "POST",
            data: {
                type: 'GET_FRAME'
            },

            success: function (json) {
                list = $("<ul></ul>");
                if (json['publishedRecently']) {

                    $("#detectedFaces").html(
                        "<img src='" + json['dataURL'] + "' width='430px'>"
                    );
                    $.each(json['detectedPeople'], function(index, value){
                        list.append('<li>'+value+'</li>')
                    });
                     $('#detectedPeople div').html(list)

                } else {
                    if (json['publishedRecently']) {
                        $('#detectedPeople div').html('<p>No camera.</p>')
                    }
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