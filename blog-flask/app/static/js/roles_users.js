$(document).ready(function() {
  //FUNÇÃO PRA CARREGAR LISTA PAPÉIS DE USUÁRIOS NO PAINEL ADMIN
  function load_roles_users() {
    $.ajax({
      url: "/admin/users/roles/render",
      type: "GET",
      success: function(html) {
        $("#roles").html(html);
        
        $("#roles").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }
  
  load_roles_users();
  
  //FUNÇÃO PRA PAGINAR NA LISTA DE PAPÉIS DOS USUÁRIOS
  function paginateUrl(url) {
    $.ajax({
      url: url,
      type: "GET",
      success: function(html) {
        $("#roles").html(html);
        
        $("#roles").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }
  
  //PAGINAR NA LISTA DE PAPÉIS DOS USUÁRIOS
  $("#roles").on("click", "[data-page-prev], [data-page-next]", function() {
    let url = $(this).data("page-prev") || $(this).data("page-next");
    
    paginateUrl(url);
  });
  
  //FUNÇÃO PRA CARREGAR PAPÉIS DE USUÁRIOS PESQUISADOS
  function load_search_roles_users(word) {
    $.ajax({
      url: "/admin/users/roles/search",
      type: "GET",
      data: {q: word},
      success: function(html) {
        $("#roles").html(html);
        
        $("#roles").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }
  
  //CARREGAR PAPÉIS DE USUÁRIOS PESQUISADOS
  $("#formSearchRoleUser").on("keyup", "#word", function() {
    let word = $(this).val();
    
    if(word !== "") {
      load_search_roles_users(word);
    } else {
      load_roles_users();
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
  function populateSelect(selectId, data, defaultId=null, includeEmptyOption=false) {
    const select = $(selectId).empty();
    
    // Mostra a opção fantasma
    if(includeEmptyOption) {
      select.append($("<option>", {
        value: "",
        text: "Selecione uma opção",
        disabled: true,
        selected: !defaultId
      }));
    }
    
    const options = data.map(item => 
      $("<option>", {
        value: item.id,
        text: item.name,
        selected: item.id === defaultId
      })
    );
    
    select.append(options);
    
    if(defaultId !== null) {
      selectId.val(defaultId);
    }
  }

  // Carrega as situaçôe de PAPÉIS
  $("#modalAddRoleUser").on("shown.bs.modal", function() {
    let select = $(this).find("#role_situation_id");
    
    $.ajax({
      url: "/admin/users/roles/situations/options",
      type: "GET",
      success: function(data) {
        populateSelect(select, data, 1, true);
      }
    });
  });
  
  // Cria uma função
  $("#formAddRoleUser").on("submit", function(event) {
    event.preventDefault();
    
    let $modal = $("#modalAddRoleUser");
    let $btn = $modal.find("#btnAdd");
    let btnText = $btn.text();
    let formData = new FormData(this);
    
    button_status($btn, "Adicionando...");
    
    $.ajax({
      url: "/admin/users/roles/create",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        if(res.status === "success") {
          $("#formAddRoleUser")[0].reset();
        }
        
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_roles_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });

  //AJAX - Visualizar informaçôes de função
  $("#roles").on("click", "[data-view-role-user-id]", function() {
    let role_user_id = $(this).data("view-role-user-id");
    let $modal = $("#modalViewRoleUser");
    let $spinner = $modal.find("#spinner");
    let $content = $modal.find("#modal-content");
    
    $spinner.removeClass("d-none");
    $content.addClass("d-none").empty();
    
    setTimeout(() => {
    $.ajax({
      url: `/admin/users/roles/${role_user_id}/view`,
      type: "GET",
      success: function(html) {
        $content.html(html);
        $content.removeClass("d-none");
        $spinner.addClass("d-none");
        
        //Formata a data de controle do registro
        $content.find(".created, .modified").each(function() {
          let dataText = $(this).text().trim();
          let formattedText = formatData(dataText);
          $(this).text(formattedText);
        });
      }
    });
    }, 300);
  });
  
  //AJAX - BUSCAR DADOS DA FUNÇÃO PARA PREENCHER O FORMULÁRIO NA MODAL
  $("#roles").on("click", "[data-edit-role-user-id]",function() {
    let role_id = $(this).data("edit-role-user-id");
    let $modal = $("#modalEditRoleUser");
    let $form = $modal.find("#formEditRoleUser");
    
    $form.data("role_id", role_id);
    
    $.ajax({
      url: `/admin/users/roles/${role_id}/data`,
      type: "GET",
      success: function(data) {
        //Guarda dados do servidor em constantes
        const role = data.role;
        const role_situations = data.role_situations;
        
        //Preenche os campos do formulario(somente checkbox e input)
        fillFormFields("#modalEditRoleUser", role);
        
        //Monta um select com situaçôes
        let select_rs = $form.find("#role_situation_id");
        
        populateSelect(select_rs, role_situations, role.role_situation_id, true);
      }
    });
  });

  //Atualiza uma situação
  $("#formEditRoleUser").on("submit", function(event) {
    event.preventDefault();
    
    let $modal = $("#modalEditRoleUser");
    let $btn = $modal.find("#btnEdit");
    let btnText = $btn.text();
    let formData = new FormData(this);
    let role_id = $(this).data("role_id");
    
    button_status($btn, "Atualizando...");
    
    $.ajax({
      url: `/admin/users/roles/${role_id}/update`,
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        if(res.status === "success") {
          $("#formEditRoleUser")[0].reset();
        }
        
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_roles_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });
  
  // Daqui pra baixo é codigo reaproveitado:
  
  //Seleciona um cargo para ser excluido
  $("#roles").on("click", "[data-delete-role-user-id]", function() {
    let $modal = $("#modalDeleteRoleUser");
    let role_id = $(this).data("delete-role-user-id");
  
    $modal.find("#btnConfirm").data("role_id", role_id);
  });
  
  //Excluir um cargo
  $("#modalDeleteRoleUser #btnConfirm").on("click", function() {
    let role_id = $(this).data("role_id");
    let $modal = $("#modalDeleteRoleUser");
    let $btn = $modal.find("#btnConfirm");
    let btnText = $btn.text();
  
    button_status($btn, "Excluindo...");
    
    $.ajax({
      url: `/admin/roles/${role_id}/delete`,
      type: "POST",
      success: function(res) {
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_roles_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });
});