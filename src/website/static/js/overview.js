window.onload = function () {
    $(".btn-delete-hero").bind("click", function (event) {
        if (confirm("You sure?")) {
            let csrf = $("#csrf_token").val();
            fetch("/delete-hero", {
                method: "POST",
                headers: {
                    "Content-type": "application/json",
                    "X-CSRF-TOKEN": csrf,
                },
                body: JSON.stringify({ "name": event.currentTarget.id }),
            })
                .then((res) => {
                    if (res.ok) return res.json();
                    else alert("Something went wront");
                })
                .then((jsonResponse) => {
                    if (jsonResponse["error"] == 0) {
                        event.currentTarget.parentElement.remove();
                    } else {
                        alert("Could not delete that element");
                    }
                });
        }
    });
};
