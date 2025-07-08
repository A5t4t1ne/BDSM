/**
 * Manually display a dismissable alert message.
 * @param {string} message
 * @param {string} type either "success" or "danger"
 */
function alertMessage(message, type) {
    let innerHTML = [
        `<div class="alert alert-${type} alert-dismissible fade show" role="alert"  data-autohide="true" data-delay="2000">`,
        `   <div>${message}</div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        "</div>",
    ].join("");

    $("#alert-container").html(innerHTML);
}
