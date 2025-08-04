$(document).ready(function() {
  //FORMATA A DATA VINDA DO SERVIDOR
  function formatData(dataText) {
    let fromNowTextCreated = moment.utc(dataText).fromNow();
    return fromNowTextCreated;
  }
  
  //FUNÇÃO PRA CARREGAR LISTA COMENTÁRIOS DE ARTIGO NO PAINEL ADMIN
  function load_articles_comments() {
    $.ajax({
      url: "/dashboard/articles/comments/render",
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
  
  load_articles_comments();
  
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
  
});