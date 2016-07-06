
$('document').ready(function() {
    $('tr').click( function() {
        window.location = '/openface/detectedpeople/' + $(this).find('.pk').html();
    })
});