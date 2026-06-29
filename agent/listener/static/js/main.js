$(document).ready(function() {

	// Default page content helpers
	$('body').tooltip({ html: true, selector: '.tt-bind', container: 'body' });
    $('body').popover({ html: true, selector: '.pop-bind', trigger: 'focus', container: 'body' });

    if ($('body').data('session-monitor')) {
        var sessionTimer = null;

        function refreshOnSessionExpiry() {
            window.location.href = '/login';
        }

        function scheduleSessionRefresh(expiresAt) {
            if (sessionTimer) {
                clearTimeout(sessionTimer);
            }
			
            var delay = Math.floor(expiresAt * 1000) - Date.now();
            if (delay <= 0) {
                refreshOnSessionExpiry();
                return;
            }
            sessionTimer = setTimeout(refreshOnSessionExpiry, delay);
        }

        function checkSessionStatus() {
            $.ajax({
                url: '/gui/session/status',
                dataType: 'json',
                cache: false
            }).done(function(data) {
                if (!data.logged) {
                    refreshOnSessionExpiry();
                    return;
                }

                if (data.expires_at) {
                    scheduleSessionRefresh(data.expires_at);
                }
            }).fail(function(xhr) {
                if (xhr.status === 401) {
                    refreshOnSessionExpiry();
                }
            });
        }

        var expiresAt = parseFloat($('body').data('session-expires-at'), 10);
        if (!isNaN(expiresAt)) {
            scheduleSessionRefresh(expiresAt);
        }

        checkSessionStatus();
        setInterval(checkSessionStatus, 60000);
    }

});