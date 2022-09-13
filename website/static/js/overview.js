window.onload = function () {
    $(".hero-deletable .btn-close").bind("click", function (event) {
        if (confirm("You sure?")) {
            fetch("/delete-hero", {
                method: "POST",
                headers: {
                    "Content-type": "application/json",
                    // "Accept": "application/json",
                },
                body: JSON.stringify({ "id": event.currentTarget.id }),
            });
        }
        console.log(event);
        event.currentTarget.parentElement.remove();
    });
};
