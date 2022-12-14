var current_wealth = {
    d: 0,
    s: 0,
    h: 0,
    k: 0,
};

function get_current_hero(event) {
    fetch("/data-request", {
        method: "POST",
        headers: {
            "Content-type": "application/json",
            "Accept": "application/json",
        },
        body: JSON.stringify({ "id": event.currentTarget.value }),
    })
        .then((res) => {
            if (res.ok) return res.json();
            else alert("Something went wront");
        })
        .then((jsonResponse) => {
            update_new_hero_stats(jsonResponse);
        });
}

window.onload = function () {
    // set initial value
    let hero_select = $(".hero-select");
    if (hero_select.currentTarget.value !== -1) {
        let curr_hero = get_current_hero(hero_select);
    }
    hero_select.on("change", get_current_hero);

    $(".money-input").bind("change", update_money);
};

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
    let total_k_money = 1000 * curr_d + 100 * curr_s + 10 * curr_h + curr_k;
    current_wealth = splitMoney(total_k_money);

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

function update_new_hero_stats(hero) {
    $("#lep-max").text(hero["lep_max"]);
    $("#asp-max").text(hero["asp_max"]);
    $("#kap-max").text(hero["kap_max"]);
    $("#money-d").text(hero["wealth"]["d"]);
    $("#money-s").text(hero["wealth"]["s"]);
    $("#money-h").text(hero["wealth"]["h"]);
    $("#money-k").text(hero["wealth"]["k"]);
    $("#armor").text(hero["armor"]);
    // $('#dodge').text(hero['dodge']);     !not implemented yet
    // $('initiative').text(hero['base_attr']['INI'])   !not implemented yet
    $("#encumbrance").text(hero["enc"]);
    // implement pain

    console.log(hero);
}
