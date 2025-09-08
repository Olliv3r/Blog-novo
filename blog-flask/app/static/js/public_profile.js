$(document).ready(function() {
  // Enviar mensagem
  $("#formMessage").on("submit", function(event) {
    event.preventDefault();
    
    var $form = $(this);
    var formData = $form.serialize();
    
    $.ajax({
      url: $form.attr("action"),
      type: "POST",
      data: formData,
      success: function(response) {
        alertt("#user_message", response.color, response.message);
        $form[0].reset();
        $("#messageModal").modal("hide");
      }
    })
  });
});