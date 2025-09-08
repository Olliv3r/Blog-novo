$(document).ready(function() {
  // APRESENTAR OU OCULTAR MENU
  $(".sidebar-toggle").on("click", function() {
    $(".sidebar").toggleClass("toggled");
  });
  
  // CARREGAR ABERTO SUBMENU
  var active = $(".sidebar .active");
  
  if (active.length && active.parent(".collapse").length) {
    var parent = active.parent(".collapse");
    
    parent.prev("a").attr("aria-expanded", true);
    parent.addClass("show");
  }
  
});