window.onload = function () {
    $("#save-btn").on("click", save_hero);
};

/**
 * Send current values to webserver to save them in database
 * @param {*} evt
 */
function save_hero(obj) {
    let lep = $("#max-lep").val();
    let asp = $("#max-asp").val();
    let kap = $("#max-kap").val();
    let name = $("#secure-name").html();

    let new_hero_values = newHeroObject(lep, asp, kap, name);
    let csrf = $("#csrf_token").val();
    const response = fetch("/save-hero", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
            "X-CSRF-TOKEN": csrf,
        },
        body: JSON.stringify(new_hero_values),
    })
        .then((response) => {
            response
                .json()
                .then((data) => {
                    console.log(data);
                    let jres = data;
                    if (jres["error"] == 0) {
                        alertMessage(jres["message"], "success");
                    } else {
                        alertMessage(jres["message"], "danger");
                    }
                })
                .catch((error) => {
                    console.error("Error:", error);
                    alertMessage(
                        "Could not decode response from server",
                        "danger"
                    );
                });
        })
        .catch((error) => {
            console.error("Error:", error);
            alertMessage(
                "Could not retrieve proper message from server",
                "danger"
            );
        });

    return response;
}

/**
 * Returns a pseudo hero object for saving the current stats
 * @param {int} lep
 * @param {int} asp
 * @param {int} kap
 * @param {String} name
 * @returns
 */
function newHeroObject(lep, asp, kap, name) {
    let stats = {
        "lep_max": lep,
        "asp_max": asp,
        "kap_max": kap,
        "name": name,
    };
    return stats;
}
