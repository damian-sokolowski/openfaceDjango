$('document').ready(function() {
    $('#table').DataTable();
    $('#table tbody tr').click( function() {
        window.location = '/openface/addedpeople/' + $(this).find('.pk').html();
    })
});