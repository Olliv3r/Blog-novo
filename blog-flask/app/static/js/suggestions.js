$(document).ready(function() {
  //FUNÇÃO PRA CARREGAR LISTA DE SUGESTÔES NO PAINEL ADMIN
  function load_suggestions() {
    let $suggestions = $("#suggestions");
    
    $.ajax({
      url: "/dashboard/suggestions/render",
      type: "GET",
      success: function(html) {
        $suggestions.html(html);
        $suggestions.find(".created").each(function() {
          let dataText = $(this).text();
  
          $(this).text(formatData(dataText));
        });
      }
    });
  }
  
  load_suggestions();
  
  /*
  //FUNÇÃO PRA PAGINAR NA LISTA DE COMENTÁRIOS DOS ARTIGO
  function paginateUrl(url) {
    $.ajax({
      url: url,
      type: "GET",
      success: function(html) {
        $("#articles_comments").html(html);
        
        $("#articles_comments").find(".created").each(function() {
          let dataText = $(this).text();
          
          $(this).text(formatData(dataText));
        });
      }
    });
  }
  
  //PAGINAR NA LISTA DE COMENTÁRIOS DOS ARTIGOS
  $("#articles_comments").on("click", "[data-page-prev], [data-page-next]", function() {
    let url = $(this).data("page-prev") || $(this).data("page-next");
    
    paginateUrl(url);
  });
  
  //FUNÇÃO PRA CARREGAR COMENTÁRIOS DE ARTIGOS PESQUISADOS
  function load_search_articles_comments(word) {
    $.ajax({
      url: "/dashboard/articles/comments/search",
      type: "GET",
      data: {word: word},
      success: function(html) {
        $("#articles_comments").html(html);
        
        $("#articles_comments").find(".created").each(function() {
          let dataText = $(this).text();
          
          $(this).text(formatData(dataText));
        });
      }
    });
  }
  
  //CARREGAR COMENTÁRIOS DE ARTIGOS PESQUISADOS
  $("#formSearchComment").on("keyup", "#word", function() {
    let word = $(this).val();
    
    if(word !== "") {
      load_search_articles_comments(word);
    } else {
      load_articles_comments();
    }
  });
  */
});