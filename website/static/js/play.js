window.onload = function () {
    let hero_select = $(".hero-select");
    hero_select.on("change", get_hero_and_update);
    hero_select.on("click", save_hero);
    // set initial value
    if (hero_select.val() !== -1) {
        get_hero_and_update(hero_select);
    }

    $(".money-input").on("change", update_money);
    $("#lep").bind("change", function (evt) {
        let curr = $("#lep").val();
        let max = $("#lep-max").text();
        console.log(curr, max);
        $("#pain").text(getPainLvl(curr, max));
    });
    setInterval(save_hero, 15000); // save hero every 15 seconds
};

/**
 * Sends a post request to get the new hero values and sets them.
 * @param {*} obj jQuery event or select object
 */
function get_hero_and_update(obj) {
    let name = "";
    try {
        name = obj.val();
    } catch (error) {
        name = obj.target.value;
    }

    fetch("/data-request", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
        },
        body: JSON.stringify({ "name": name }),
    })
        .then((res) => {
            if (res.ok) return res.json();
            else alert("Something went wront");
        })
        .then((jsonResponse) => {
            update_new_hero_stats(jsonResponse);
        });
}

/**
 * Send current values to webserver to save them in database
 * @param {*} evt
 */
function save_hero(obj) {
    let wealth = get_money();

    let hero_stats = newHeroObject(
        $("#lep").val(),
        $("#asp").val(),
        $("#kap").val(),
        $(".hero-select").val(),
        wealth
    );

    const response = fetch("/save-hero", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
        },
        body: JSON.stringify(hero_stats),
    });

    return response;
}

/**
 * returns the current amount of money in an object
 */
function get_money() {
    let d = $("#money-d").val();
    let s = $("#money-s").val();
    let h = $("#money-h").val();
    let k = $("#money-k").val();

    return { d, s, h, k };
}

/**
 * Handles the money change from a user
 * @param {*} event
 */
function update_money() {
    // get the current amount of money
    let d = $("#money-d").val();
    let s = $("#money-s").val();
    let h = $("#money-h").val();
    let k = $("#money-k").val();

    // check if the values are valid
    let money = { d, s, h, k };
    for (let key in money) {
        let val = parseInt(money[key]);
        if (isNaN(val) || val < 0) {
            money[key] = 0;
        } else {
            money[key] = val;
        }
    }

    // just for shortening
    d = money.d;
    s = money.s;
    h = money.h;
    k = money.k;

    // rearange the money
    let total = d * 1000 + s * 100 + h * 10 + k;
    d = Math.floor(total / 1000);
    s = Math.floor((total % 1000) / 100);
    h = Math.floor((total % 100) / 10);
    k = Math.floor(total % 10);

    // update the input fields
    $("#money-d").val(d);
    $("#money-s").val(s);
    $("#money-h").val(h);
    $("#money-k").val(k);
}

/**
 * Reformat the total money and return it in a dictionary
 * @param {*} money
 * @returns money split up tp d, h, s, k
 */
function splitMoney(money) {
    if (money === 0) return { "d": 0, "s": 0, "h": 0, "k": 0 };

    let smoney = String(money);

    let d = Number(smoney.slice(0, smoney.length - 3));
    let remain = smoney.slice(smoney.length - 3);

    let s = Number(remain[0]);
    let h = Number(remain[1]);
    let k = Number(remain[2]);
    return { d, s, h, k };
}

/**
 * Returns the pain value based on live points
 * @param {int} current
 * @param {int} max
 */
function getPainLvl(current, max) {
    if (current <= 5) {
        return 4;
    }
    if (current <= max * 0.25) {
        return 3;
    }
    if (current <= max * 0.5) {
        return 2;
    }
    if (current <= max * 0.75) {
        return 1;
    }
    return 0;
}

/**
 * updates all the values on the screen with the values from the given hero
 * @param {*} hero hero in json format
 */
function update_new_hero_stats(hero) {
    // life, magic, holyness
    $("#lep-max").text(hero["lep_max"]);
    $("#asp-max").text(hero["asp_max"]);
    $("#kap-max").text(hero["kap_max"]);
    $("#lep").val(hero["lep_current"]);
    $("#asp").val(hero["asp_current"]);
    $("#kap").val(hero["kap_current"]);
    $("#money-d").val(hero["wealth"]["d"]);
    $("#money-s").val(hero["wealth"]["s"]);
    $("#money-h").val(hero["wealth"]["h"]);
    $("#money-k").val(hero["wealth"]["k"]);
    $("#armor").text(hero["armor"]);
    $("#dodge").text(hero["dodge"]);
    $("#initiative").text(hero["INI"]);

    // effects
    $("#encumbrance").text(hero["enc"]);
    $("#pain").val(getPainLvl(hero["lep_current"], hero["lep_max"]));
}

/**
 * Returns a pseudo hero object for saving the current stats
 * @param {int} lep
 * @param {int} asp
 * @param {int} kap
 * @param {dict} wealth a dictionary
 * @returns
 */
function newHeroObject(lep, asp, kap, name, wealth) {
    let stats = {
        "lep_current": lep,
        "asp_current": asp,
        "kap_current": kap,
        "name": name,
        "wealth": wealth,
    };
    return stats;
}
