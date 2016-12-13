$(document).ready(function() {
    $(document).keydown(function(e) {
        if (e.keyCode == 82 && e.ctrlKey || e.keyCode == 116) {
            if (window.self !== window.top) {
                location.reload(true);
            } else {
                document.getElementById('help-iframe').contentWindow.location.reload(true);
            }
            return false;
        }
    });
});