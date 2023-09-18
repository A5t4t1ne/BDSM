let current_hero_values = 0;

window.onload = function () {
    let hero_select = $(".hero-select");
    hero_select.on("change", get_hero_and_update);
    hero_select.on("click", update_current_hero);
    hero_select.on("change", save_hero);
    // set initial value
    if (hero_select.val() !== -1) {
        get_hero_and_update(hero_select);
    }

    $(".money-input").on("change", update_money);
    $("#lep").bind("change", function (evt) {
        let curr = $("#lep").val();
        let max = $("#lep-max").text();
        $("#pain").text(getPainLvl(curr, max));
    });
    // setInterval(save_hero, 1000); // save hero every second
};

function update_current_hero(obj) {
    let wealth = get_money();

    current_hero_values = newHeroObject(
        $("#lep").val(),
        $("#asp").val(),
        $("#kap").val(),
        $(".hero-select").val(),
        wealth,
        $("#schips").val()
    );
}

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

    let csrf = $("#csrf_token").val();
    fetch("/data-request", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
            "X-CSRF-TOKEN": csrf,
        },
        body: JSON.stringify({ "name": name }),
    })
        .then((res) => {
            if (res.ok) return res.json();
            else
                alertMessage(
                    "Could not retrieve proper message from server",
                    "danger"
                );
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
    let csrf = $("#csrf_token").val();
    const response = fetch("/save-hero", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
            "X-CSRF-TOKEN": csrf,
        },
        body: JSON.stringify(current_hero_values),
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
        if (isNaN(val)) {
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
    if (total >= 0) {
        d = Math.floor(total / 1000);
        s = Math.floor((total % 1000) / 100);
        h = Math.floor((total % 100) / 10);
        k = Math.floor(total % 10);

        // update the input fields
        $("#money-d").val(d);
        $("#money-s").val(s);
        $("#money-h").val(h);
        $("#money-k").val(k);
    } else {
        alert("Not enough money");
    }
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
    $("#schips").val(hero["schips"]);
    $("#armor").text(hero["armor"]);
    $("#dodge").text(hero["dodge"]);
    $("#initiative").text(hero["INI"]);

    // effects
    $("#encumbrance").text(hero["enc"]);
    $("#pain").val(getPainLvl(hero["lep_current"], hero["lep_max"]));

    function update_liturgies() {
        let liturgic_content = "";
        let lit_keys = Object.keys(hero["liturgies"]);
        let bl_keys = Object.keys(hero["blessings"]);
        lit_keys.sort(function (a, b) {
            a = hero["liturgies"][a]["name"];
            b = hero["liturgies"][b]["name"];
            if (a < b) return -1;
            if (a > b) return 1;
            return 0;
        });
        bl_keys.sort(function (a, b) {
            a = hero["blessings"][a]["name"];
            b = hero["blessings"][b]["name"];
            if (a < b) return -1;
            if (a > b) return 1;
            return 0;
        });

        let keys = lit_keys.concat(bl_keys);

        keys.forEach((key) => {
            let lit_stats = "";
            let checks = "";
            let check1 = "";
            let check2 = "";
            let check3 = "";
            let castingTime = "";
            let fw = "";
            // console.log(hero);
            // console.log(hero["activatables"]);
            if (key.indexOf("BLESSING") == 0) {
                lit_stats = hero["blessings"][key];
            } else if (key.indexOf("LITURGY") == 0) {
                lit_stats = hero["liturgies"][key];
                // checks for liturgies who have dice checks
                if (lit_stats["univ"]["check1"]) {
                    check1 = lit_stats["univ"]["check1"]["short"];
                    check2 = lit_stats["univ"]["check2"]["short"];
                    check3 = lit_stats["univ"]["check3"]["short"];
                }
                castingTime = lit_stats["castingTime"];
                fw = lit_stats["FW"];
                checks = check1 + " / " + check2 + " / " + check3;
            }

            liturgic_content +=
                '<div class="row activatable">' +
                `<div class="col">${lit_stats["name"]}</div>` +
                `<div class="col text-center">${castingTime}</div>` +
                `<div class="col text-end">${lit_stats["duration"]}</div>` +
                `<div class="col text-center">${fw}</div>` +
                `<div class="col text-end">${checks}</div>` +
                "</div>";
        });

        $("#liturgies-content").html(liturgic_content);
    }

    function update_spells() {
        let spell_content = "";
        let spell_keys = Object.keys(hero["spells"]);

        spell_keys.sort(function (a, b) {
            a = hero["spells"][a]["name"];
            b = hero["spells"][b]["name"];
            if (a < b) return -1;
            if (a > b) return 1;
            return 0;
        });
        fw = 3;
        spell_keys.forEach((key) => {
            spell_stats = hero["spells"][key];
            // console.log(hero.spells, spell_stats);

            let check1 = spell_stats["univ"]["check1"]["short"];
            let check2 = spell_stats["univ"]["check2"]["short"];
            let check3 = spell_stats["univ"]["check3"]["short"];
            let checks = check1 + " / " + check2 + " / " + check3;

            spell_content +=
                '<div class="row activatable">' +
                `<div class="col">${spell_stats["name"]}</div>` +
                `<div class="col text-center">${spell_stats["castingTime"]}</div>` +
                `<div class="col text-end">${spell_stats["duration"]}</div>` +
                `<div class="col text-center">${fw}</div>` +
                `<div class="col text-end">${checks}</div>` +
                "</div>";
        });
        $("#spells-content").html(spell_content);
    }

    function update_special_abilities() {
        let sa_content = "<p>Yo wassup</p>";
        let sa_keys = Object.keys(hero["activatables"]["SA"]);
        // console.log(sa_keys);
        // sa_keys.sort(function (a, b) {
        //     a = hero["liturgies"][a]["name"];
        //     b = hero["liturgies"][b]["name"];
        //     if (a < b) return -1;
        //     if (a > b) return 1;
        //     return 0;
        // });
        // bl_keys.sort(function (a, b) {
        //     a = hero["blessings"][a]["name"];
        //     b = hero["blessings"][b]["name"];
        //     if (a < b) return -1;
        //     if (a > b) return 1;
        //     return 0;
        // });
        // let keys = sa_keys.concat(bl_keys);
        // keys.forEach((key) => {
        //     let lit_stats = "";
        //     let checks = "";
        //     let check1 = "";
        //     let check2 = "";
        //     let check3 = "";
        //     let castingTime = "";
        //     let fw = "";
        //     if (key.indexOf("BLESSING") == 0) {
        //         lit_stats = hero["blessings"][key];
        //     } else if (key.indexOf("LITURGY") == 0) {
        //         lit_stats = hero["liturgies"][key];
        //         // checks for liturgies who have dice checks
        //         if (lit_stats["univ"]["check1"]) {
        //             check1 = lit_stats["univ"]["check1"]["short"];
        //             check2 = lit_stats["univ"]["check2"]["short"];
        //             check3 = lit_stats["univ"]["check3"]["short"];
        //         }
        //         castingTime = lit_stats["castingTime"];
        //         fw = lit_stats["FW"];
        //         checks = check1 + " / " + check2 + " / " + check3;
        //     }
        //     sa_content +=
        //         '<div class="row activatable">' +
        //         `<div class="col">${lit_stats["name"]}</div>` +
        //         `<div class="col text-center">${castingTime}</div>` +
        //         `<div class="col text-end">${lit_stats["duration"]}</div>` +
        //         `<div class="col text-center">${fw}</div>` +
        //         `<div class="col text-end">${checks}</div>` +
        //         "</div>";
        // });
        $("#sa-content").html(sa_content);
    }

    update_liturgies();
    update_spells();
    update_special_abilities();
}

/**
 * Returns a pseudo hero object for saving the current stats
 * @param {int} lep
 * @param {int} asp
 * @param {int} kap
 * @param {dict} wealth
 * @returns
 */
function newHeroObject(lep, asp, kap, name, wealth, schips) {
    let stats = {
        "lep_current": lep,
        "asp_current": asp,
        "kap_current": kap,
        "name": name,
        "wealth": wealth,
        "schips": schips,
    };
    return stats;
}
