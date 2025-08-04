$(document).ready(function() {
  //FUNÇÃO PRA CARREGAR LISTA ARTIGOS NO PAINEL ADMIN
  function load_articles() {
    $.ajax({
      url: "/dashboard/articles/render",
      type: "GET",
      success: function(html) {
        $("#articles").html(html);
        
        $("#articles").find(".created").each(function() {
          let dataText = $(this).text();
          
          $(this).text(formatData(dataText));
        });
      }
    });
  }
  
  load_articles();
  
  //FUNÇÃO PRA PAGINAR NA LISTA DE ARTIGOS
  function paginateUrl(url) {
    $.ajax({
      url: url,
      type: "GET",
      success: function(html) {
        $("#articles").html(html);
        
        $("#articles").find(".created").each(function() {
          let dataText = $(this).text();
          
          $(this).text(formatData(dataText));
        });
      }
    });
  }
  
  //PAGINAR NA LISTA DE ARTIGOS
  $("#articles").on("click", "[data-page-prev], [data-page-next]", function() {
    let url = $(this).data("page-prev") || $(this).data("page-next");
    
    paginateUrl(url);
  });
  
  //FUNÇÃO PRA CARREGAR ARTIGOS PESQUISADOS
  function load_search_articles(word) {
    $.ajax({
      url: "/dashboard/articles/search",
      type: "GET",
      data: {word: word},
      success: function(html) {
        $("#articles").html(html);
        
        $("#articles").find(".created").each(function() {
          let dataText = $(this).text();
          
          $(this).text(formatData(dataText));
        });
      }
    });
  }
  
  //CARREGAR ARTIGOS PESQUISADOS
  $("#formSearchArticle").on("keyup", "#word", function() {
    let word = $(this).val();
    
    if(word !== "") {
      load_search_articles(word);
    } else {
      load_articles();
    }
  });
  
  let blockIndex = 0;

  $('#addBlockBtn').on('click', function () {
    const type = $('#blockTypeSelect').val();
    const index = blockIndex++;
  
    let blockHtml = `
      <div class="card mb-3 block-form" data-index="${index}">
        <div class="card-header d-flex justify-content-between align-items-center">
          <strong>Bloco: ${type}</strong>
          <button type="button" class="btn btn-sm btn-danger remove-block">Remover</button>
        </div>
        <div class="card-body">
    `;
  
    if (type === 'text') {
      blockHtml += `
        <div class="mb-3">
          <label>Título</label>
          <input type="text" name="blocks[${index}][title]" class="form-control">
        </div>
        <div class="mb-3">
          <label>Parágrafo</label>
          <textarea name="blocks[${index}][content]" class="form-control"></textarea>
        </div>
      `;
    } else if (type === 'image') {
      blockHtml += `
        <div class="mb-3">
          <label>Legenda</label>
          <input type="text" name="blocks[${index}][caption]" class="form-control">
        </div>
        <div class="mb-3">
          <label>Imagem</label>
          <input type="file" name="blocks[${index}][image]" class="form-control">
        </div>
      `;
    } else if (type === 'quote') {
      blockHtml += `
        <div class="mb-3">
          <label>Citação</label>
          <input type="text" name="blocks[${index}][quote]" class="form-control">
        </div>
        <div class="mb-3">
          <label>Autor</label>
          <input type="text" name="blocks[${index}][author]" class="form-control">
        </div>
      `;
    }
  
    blockHtml += `</div></div>`;
  
    $('#blocksContainer').append(blockHtml);
  });
  
  // Remover bloco
  $(document).on('click', '.remove-block', function () {
    $(this).closest('.block-form').remove();
  });

  // Enviar formulário
  $('#formAddArticle').submit(function (e) {
    e.preventDefault();

    // Pega dados do artigo
    const articleData = {
      title: $('input[name="article_title"]').val(),
      situation: $('input[name="situation_article"]').val(),
      blocks: []
    };

    // Pega dados dos blocos
    $('#blocks-container .block').each(function () {
      const type = $(this).data('type');
      const content = $(this).find('.block-content').val();
      articleData.blocks.push({ type, content });
    });

    // Envia via AJAX
    $.ajax({
      url: '/salvar_artigo',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(articleData),
      success: function (res) {
        alert('Artigo salvo com sucesso!');
        console.log(res);
      },
      error: function (err) {
        alert('Erro ao salvar!');
        console.error(err);
      }
    });
  });
});
});