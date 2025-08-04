
function button_status(button, text, status=true) {
  $(button).text(text);
  $(button).prop("disabled", status);
}