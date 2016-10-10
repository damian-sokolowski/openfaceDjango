$('document').ready(function() {
    $('#table').DataTable();
    $('#table tbody tr').click( function() {
        window.location = '/openface/detectedpeople/' + $(this).find('.pk').html();
    })
});