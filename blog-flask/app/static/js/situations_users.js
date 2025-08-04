$(document).ready(function() {
  //FUNÇÃO PRA CARREGAR LISTA SITUAÇÔES DE USUÁRIOS NO PAINEL ADMIN
  function load_situations_users() {
    $.ajax({
      url: "/dashboard/users/situations/render",
      type: "GET",
      success: function(html) {
        $("#situations").html(html);
        
        $("#situations").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedData = formatData(dataText);
          
          $(this).text(formattedData);
        });
      }
    });
  }
  
  load_situations_users();
  
  //FUNÇÃO PRA PAGINAR NA LISTA DE SITUAÇÔES DOS USUÁRIOS
  function paginateUrl(url) {
    $.ajax({
      url: url,
      type: "GET",
      success: function(html) {
        $("#situations").html(html);
        
        $("#situations").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedData = formatData(dataText);
          
          $(this).text(formattedData);
        });
      }
    });
  }
  
  //PAGINAR NA LISTA DE SITUAÇÔES DOS USUÁRIOS
  $("#situations").on("click", "[data-page-prev], [data-page-next]", function() {
    let url = $(this).data("page-prev") || $(this).data("page-next");
    
    paginateUrl(url);
  });
  
  //FUNÇÃO PRA CARREGAR SITUAÇÔES DE USUÁRIOS PESQUISADOS
  function load_search_situations_users(word) {
    $.ajax({
      url: "/dashboard/users/situations/search",
      type: "GET",
      data: {word: word},
      success: function(html) {
        $("#situations").html(html);
        
        $("#situations").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedData = formatData(dataText);
          
          $(this).text(formattedData);
        });
      }
    });
  }
  
  //CARREGAR SITUAÇÔES DE USUÁRIOS PESQUISADOS
  $("#formSearchSituationUser").on("keyup", "#word", function() {
    let word = $(this).val();
    
    if(word !== "") {
      load_search_situations_users(word);
    } else {
      load_situations_users();
    }
  });
  
  //PREENCHE UM FORMULÁRIO
  function fillFormFields(formSelector, data) {
    Object.entries(data).forEach(([key, value]) => {
      const $el = $(`${formSelector} #${key}`);
      
      if(!$el.length) return;
      
      if($el.is(":checkbox")) {
         $el.prop("checked", !!value);
      } else {
        $el.val(value);
      }
    });
  }
  
  //MONTA UM SELECT
  function populateSelect(selectId, data, defaultValue=null, includeEmptyOption=false) {
    const select = $(selectId).empty();
    
    // Mostra a opção fantasma
    if(includeEmptyOption) {
      select.append($("<option>", {
        value: "",
        text: "Selecione uma opção",
        disabled: true,
        selected: !defaultValue
      }));
    }
    
    const options = data.map(item => 
      $("<option>", {
        value: item,
        text: item.charAt(0).toUpperCase() + item.slice(1),
        selected: item === defaultValue
      })
    );
    
    select.append(options);
    
    if(defaultValue !== null) {
      selectId.val(defaultValue);
    }
  }
  
  // Cria uma entidade
  $("#formAddSituationUser").on("submit", function(event) {
    event.preventDefault();
    
    let $modal = $("#modalAddSituationUser");
    let $btn = $modal.find("#btnAdd");
    let btnText = $btn.text();
    let formData = new FormData(this);
    
    button_status($btn, "Adicionando...");
    
    $.ajax({
      url: "/dashboard/situations/create",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        if(res.status === "success") {
          $("#formAddSituationUser")[0].reset();
        }
        
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_situations_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });

  //AJAX - Visualizar informaçôes de situação
  $("#situations").on("click", "[data-view-situation-user-id]", function() {
    let situation_user_id = $(this).data("view-situation-user-id");
    let $modal = $("#modalViewSituationUser");
    let $spinner = $modal.find("#spinner");
    let $content = $modal.find("#modal-content");
    
    $spinner.removeClass("d-none");
    $content.addClass("d-none").empty();
    
    setTimeout(() => {
    $.ajax({
      url: `/dashboard/users/situations/${situation_user_id}/view`,
      type: "GET",
      success: function(html) {
        $content.html(html);
        $content.removeClass("d-none");
        $spinner.addClass("d-none");
        
        //Formata a data de controle de registros
        $content.find(".created, .modified").each(function() {
          let dataText = $(this).text().trim();
          let formattedText = formatData(dataText);
          $(this).text(formattedText);
        });
      }
    });
    }, 300);
  });
  
  //AJAX - BUSCAR DADOS DA SITUAÇÃO PARA PREENCHER O FORMULÁRIO NA MODAL
  $("#situations").on("click", "[data-edit-situation-user-id]",function() {
    let situation_id = $(this).data("edit-situation-user-id");
    let $modal = $("#modalEditSituationUser");
    let $form = $modal.find("#formEditSituationUser");
    
    $form.data("situation_id", situation_id);
    
    $.ajax({
      url: `/dashboard/users/situations/${situation_id}/data`,
      type: "GET",
      success: function(data) {
        //Guarda dados do servidor em constantes
        const situation = data.situation;
        
        //Preenche os campos do formulario(somente checkbox e input)
        fillFormFields("#modalEditSituationUser", situation);
      }
    });
  });

  //Atualiza uma situação
  $("#formEditSituationUser").on("submit", function(event) {
    event.preventDefault();
    
    let $modal = $("#modalEditSituationUser");
    let $btn = $modal.find("#btnEdit");
    let btnText = $btn.text();
    let formData = new FormData(this);
    let situation_id = $(this).data("situation_id");
    
    button_status($btn, "Atualizando...");
    
    $.ajax({
      url: `/dashboard/situations/${situation_id}/update`,
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        if(res.status === "success") {
          $("#formEditSituationUser")[0].reset();
        }
        
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_situations_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });
  
  //Seleciona uma situação para ser excluida
  $("#situations").on("click", "[data-delete-situation-user-id]", function() {
    let $modal = $("#modalDeleteSituationUser");
    let situation_id = $(this).data("delete-situation-user-id");
  
    $modal.find("#btnConfirm").data("situation_id", situation_id);
  });
  
  //Excluir usuário
  $("#modalDeleteSituationUser #btnConfirm").on("click", function() {
    let situation_id = $(this).data("situation_id");
    let $modal = $("#modalDeleteSituationUser");
    let $btn = $modal.find("#btnConfirm");
    let btnText = $btn.text();
  
    button_status($btn, "Excluindo...");
    
    $.ajax({
      url: `/dashboard/situations/${situation_id}/delete`,
      type: "POST",
      success: function(res) {
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_situations_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });
});