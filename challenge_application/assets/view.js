CTFd._internal.challenge.data = undefined;

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.renderer = null;

CTFd._internal.challenge.preRender = function () {
};

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.render = null;

CTFd._internal.challenge.postRender = function () {
    var challenge_id = CTFd._internal.challenge.data.id;
    var url = "/api/v1/plugins/challenge-application/status/" + challenge_id;

    CTFd.fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        processResponse(response);
    });
};

CTFd._internal.challenge.start = function () {
    var challenge_id = CTFd._internal.challenge.data.id;
    var url = "/api/v1/plugins/challenge-application/start/" + challenge_id;

    CTFd.lib.$('#challenge-application-start').text("Waiting...");
    CTFd.lib.$('#challenge-application-start').prop('disabled', true);

    CTFd.fetch(url, {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response.json();
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response.json();
        }
        return response.json();
    }).then(function (response) {
        if (response.success) {
            CTFd._functions.events.eventAlert({
                title: "Success",
                html: "Your instance has been started! Please wait.",
                button: "OK"
            });
        }
        processResponse(response);
    });
};

CTFd._internal.challenge.submit = function (preview) {
    var challenge_id = parseInt(CTFd.lib.$("#challenge-id").val());
    var submission = CTFd.lib.$("#challenge-input").val();

    var body = {
        challenge_id: challenge_id,
        submission: submission
    };
    var params = {};
    if (preview) {
        params["preview"] = true;
    }

    return CTFd.api.post_challenge_attempt(params, body).then(function (response) {
        if (response.status === 429) {
            // User was ratelimited but process response
            return response;
        }
        if (response.status === 403) {
            // User is not logged in or CTF is paused.
            return response;
        }
        return response;
    });
};

function processResponse(response) {
    if (response.success) {
        url = response.url;
    } else {
        CTFd._functions.events.eventAlert({
            title: "Fail",
            html: response.message,
            button: "OK"
        });
    }
    if (url !== null) {
        CTFd.lib.$('#challenge-application-domain').text(url);
        CTFd.lib.$('#challenge-application-domain').attr('href', url);
        CTFd.lib.$('#challenge-application-panel-stopped').hide();
        CTFd.lib.$('#challenge-application-panel-stopped').hide();
        CTFd.lib.$('#challenge-application-panel-started').show();
        checkApplication(0);
    } else {
        CTFd.lib.$('#challenge-application-panel-stopped').show();
        CTFd.lib.$('#challenge-application-panel-started').hide();
    }
}

function checkApplication(retries) {
    var challenge_id = CTFd._internal.challenge.data.id;
    var url = "/api/v1/plugins/challenge-application/check/" + challenge_id;

    CTFd.fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    }).then(function (response) {
        if (response.status === 200) {
            CTFd.lib.$('#challenge-application-starting').hide();
            CTFd.lib.$('#challenge-application-started').show();
        } else {
            CTFd.lib.$('#challenge-application-starting').show();
            CTFd.lib.$('#challenge-application-started').hide();
            if (retries < 10) {
                retries += 1;
                setTimeout(checkApplication, 5000, retries);
            }
        }
    });
}