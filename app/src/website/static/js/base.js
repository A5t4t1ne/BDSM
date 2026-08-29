/**
 * Escape a value for safe interpolation into an HTML string.
 * Every value that originates from a hero file or the server must go through
 * this before being handed to .html().
 * @param {*} value
 * @returns {string}
 */
function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value).replace(/[&<>"'`=\/]/g, function (ch) {
        return {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;",
            "`": "&#96;",
            "=": "&#61;",
            "/": "&#47;",
        }[ch];
    });
}

/**
 * Manually display a dismissable alert message.
 * @param {string} message
 * @param {string} type either "success" or "danger"
 */
function alertMessage(message, type) {
    let innerHTML = [
        `<div class="alert alert-${type} alert-dismissible fade show" role="alert"  data-autohide="true" data-delay="2000">`,
        `   <div>${escapeHtml(message)}</div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        "</div>",
    ].join("");

    $("#alert-container").html(innerHTML);
}
