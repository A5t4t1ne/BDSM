var total_k_money = 0;
var money_states = {
    d: 0,
    s: 0,
    h: 0,
    k: 0,
};

window.onload = function () {
    $(".hero-select").bind("change", function (event) {
        // console.log(event.currentTarget.value);

        fetch("/data-request", {
            method: "POST",
            headers: {
                "Content-type": "application/json",
                "Accept": "application/json",
            },
            body: JSON.stringify({ "id": event.currentTarget.value }),
        })
            .then((res) => {
                if (res.ok) return res.json;
                else alert("Something went wront");
            })
            .then((jsonResponse) => {
                console.log(jsonResponse);
            });
    });

    $(".money-input").bind("change", update_money);
};

function update_money(event) {
    let inp_field = event.currentTarget;
    switch (inp_field.id) {
        case "money-d":
            delta = inp_field.value - money_states.d;
            total_k_money += 1000 * delta;
            money_states.d = inp_field.value;
            break;

        case "money-s":
            delta = inp_field.value - money_states.s;
            total_k_money += 100 * delta;
            money_states.s = inp_field.value;
            break;

        case "money-h":
            delta = inp_field.value - money_states.h;
            total_k_money += 10 * delta;
            money_states.h = inp_field.value;
            break;

        case "money-k":
            delta = inp_field.value - money_states.k;
            total_k_money += delta;
            money_states.k = inp_field.value;
            break;

        default:
            break;
    }

    money_states = splitMoney(total_k_money);
    let { d, s, h, k } = money_states;
    $("#money-d").val(d);
    $("#money-s").val(s);
    $("#money-h").val(h);
    $("#money-k").val(k);
}

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
