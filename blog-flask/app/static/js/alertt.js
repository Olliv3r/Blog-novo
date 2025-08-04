// Adiciona um alerta personalizado e desaparece em 6 segundos
function alertt(element, color, message = undefined) {
  $(element).addClass(`alert alert-${color}`);
  
  if (message !== undefined) {
    $(element).html(message);
  }
  
  setTimeout(function() {
    $(element).removeClass(`alert alert-${color}`);
    $(element).html("");
  }, 6000);
}
