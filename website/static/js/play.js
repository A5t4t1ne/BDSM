var current_wealth = {
    d: 0,
    s: 0,
    h: 0,
    k: 0,
};

window.onload = function () {
    // set initial value
    let hero_select = $(".hero-select");

    hero_select.bind("change", get_hero_and_update);
    if (hero_select.val() !== -1) {
        get_hero_and_update(hero_select);
    }

    $(".money-input").bind("change", update_money);
    $(".hero-stat-input").bind("change", save_hero);
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

function save_hero() {
    let hero_stats = newHeroObject(
        $("#lep").val(),
        $("#asp").val(),
        $("#kap").val(),
        $(".hero-select").val(),
        current_wealth
    );
    fetch("/save-hero", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
        },
        body: JSON.stringify(hero_stats),
    }).then((res) => {
        if (res.ok) return res.json();
        else alert("Something went wront");
    });
}

/**
 * Handles the money changee from a user input
 * @param {*} event
 */
function update_money(event) {
    let inp_field = event.currentTarget;

    switch (inp_field.id) {
        case "money-d":
            delta = inp_field.value - current_wealth.d;
            current_wealth.d += delta;
            break;

        case "money-s":
            delta = inp_field.value - current_wealth.s;
            current_wealth.s += delta;
            break;

        case "money-h":
            delta = inp_field.value - current_wealth.h;
            current_wealth.h += delta;
            break;

        case "money-k":
            delta = inp_field.value - current_wealth.k;
            current_wealth.k += delta;
            break;

        default:
            break;
    }

    let curr_d = current_wealth.d;
    let curr_s = current_wealth.s;
    let curr_h = current_wealth.h;
    let curr_k = current_wealth.k;
    let total_money = 1000 * curr_d + 100 * curr_s + 10 * curr_h + curr_k;
    current_wealth = splitMoney(total_money);

    let { d, s, h, k } = current_wealth;

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
 * updates all the values on the screen with the values from the given hero
 * @param {*} hero hero in json format
 */
function update_new_hero_stats(hero) {
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
    // $('#dodge').text(hero['dodge']);     !not implemented yet
    // $('initiative').text(hero['base_attr']['INI'])   !not implemented yet
    $("#encumbrance").text(hero["enc"]);

    // TODO: implement effects
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
        "lep": lep,
        "asp": asp,
        "kap": kap,
        "name": name,
        "wealth": wealth,
    };
    return stats;
}
