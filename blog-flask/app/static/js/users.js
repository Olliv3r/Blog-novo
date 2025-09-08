$(document).ready(function() {
  //FUNÇÃO PRA CARREGAR LISTA USUÁRIOS NO PAINEL ADMIN
  function load_users() {
    let $users = $("#users");
    
    $.ajax({
      url: "/admin/users/render",
      type: "GET",
      success: function(html) {
        $users.html(html);
        
        $users.find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }
  
  //CARREGA TODOS OS USUÁRIOS POR PADRÃO
  load_users();
  
  //FUNÇÃO PRA PAGINAR NA LISTA DE USUÁRIOS
  function paginateUrl(url) {
    $.ajax({
      url: url,
      type: "GET",
      success: function(html) {
        $("#users").html(html);
        
        $("#users").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }

  //PAGINAR NA LISTA DE USUÁRIOS
  $("#users").on("click", "[data-page-prev], [data-page-next]", function() {
    let url = $(this).data("page-prev") || $(this).data("page-next");
    
    paginateUrl(url);
  });
  
  //FUNÇÃO PRA CARREGAR USUÁRIOS PESQUISADOS
  function load_search_users(word) {
    $.ajax({
      url: "/admin/users/search",
      type: "GET",
      data: {q: word},
      success: function(html) {
        $("#users").html(html);
        
        $("#users").find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }
  
  //CARREGAR USUÁRIOS PESQUISADOS
  $("#formSearchUser").on("keyup", "#word", function() {
    let word = $(this).val();
    
    if(word !== "") {
      load_search_users(word);
    } else {
      load_users();
    }
  });
  
  //FUNÇÃO PARA MONTAR UM SELECT
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
  
  //CARREGAR AS SITUAÇÔES DE USUÁRIOS
  $("#modalAddUser").on("shown.bs.modal", function() {
    let select = $(this).find("#user_situation_id");
    
    $.ajax({
      url: "/admin/users/situations/options",
      type: "GET",
      success: function(data) {
        populateSelect(select, data, 5, true);
      }
    });
  });
  
  //CARREGAR OS PAPÉIS DE USUÁRIOS
  $("#modalAddUser").on("shown.bs.modal", function() {
    let select = $(this).find("#user_role_id");
    
    $.ajax({
      url: "/admin/users/roles/options",
      type: "GET",
      success: function(data) {
        populateSelect(select, data, 1, true);
      }
    });
  });
  
  //AJAX - CADASTRAR O USUÁRIO
  $("#modalAddUser").on("submit", "#formAddUser", function(event) {
    event.preventDefault();
    
    let $modal = $("#modalAddUser");
    let $btn = $modal.find("#btnAdd");
    let btnText = $btn.text();
    let formData = new FormData(this);
    
    button_status($btn, "Adicionando...");
    
    $.ajax({
      url: "/admin/users/create",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        if(res.status === "success") {
          $("#formAddUser")[0].reset();
        }
        
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });
  
  //AJAX - BUSCAR DADOS DO USUÁRIO PARA PREENCHER O FORMULÁRIO NA MODAL
  $("#users").on("click", "[data-edit-user-id]",function() {
    let user_id = $(this).data("edit-user-id");
    let $modal = $("#modalEditUser");
    let $form = $modal.find("#formEditUser");
    
    $form.data("user_id", user_id);
    
    $.ajax({
      url: `/admin/users/${user_id}/data`,
      type: "GET",
      success: function(data) {
        //Guarda dados do servidor em constantes
        const user = data.user;
        const situations = data.situations;
        const roles = data.roles;
        
        //Preenche os campos do formulario(somente checkbox e input)
        fillFormFields("#modalEditUser", user);
        
        //Monta um select com situaçôes e papéis
        let select_us = $form.find("#user_situation_id");
        let select_ur = $form.find("#user_role_id");
        
        populateSelect(select_us, situations, user.user_situation_id, true);
        populateSelect(select_ur, roles, user.user_role_id, true);
        
        //Impede o admin/moderador de sabotar o sistema pela interface
        const isSelf = current_user_id === user.id;
        const disabled = isSelf && (user.is_administrator || user.is_moderator);
        
        [select_us, select_ur].forEach(select => $(select).prop("disabled", disabled));
      }
    });
  });
  
  //AJAX - EDITAR O USUÁRIO
  $("#modalEditUser").on("submit", "#formEditUser", function(event) {
    event.preventDefault();
    
    let $modal = $("#modalEditUser");
    let $btn = $modal.find("#btnEdit");
    let btnText = $btn.text();
    let user_id = $modal.find("#formEditUser").data("user_id");
    let formData = new FormData(this);
    
    button_status($btn, "Atualizando...");
    
    $.ajax({
      url: `/admin/users/${user_id}/update`,
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_users();
  
        alertt("#alert", res.color, res.message);
      }
    });
  });
  
  //AJAX - Visualizar informaçôes de usuário
  $("#users").on("click", "[data-view-user-id]", function() {
    let user_id = $(this).data("view-user-id");
    let $modal = $("#modalViewUser");
    let $spinner = $modal.find("#spinner");
    let $content = $modal.find("#modal-content");
    
    $spinner.removeClass("d-none");
    $content.addClass("d-none").empty();
    
    setTimeout(() => {
    $.ajax({
      url: `/admin/users/${user_id}/view`,
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
  
  //AJAX - EXCLUIR O USUÁRIO:
  
  //Seleciona o usuário para ser excluido
  $("#users").on("click", "[data-delete-user-id]", function() {
    let $modal = $("#modalDeleteUser");
    let user_id = $(this).data("delete-user-id");
  
    $modal.find("#btnConfirm").data("user_id", user_id);
  });
  
  //Excluir usuário
  $("#modalDeleteUser #btnConfirm").on("click", function() {
    let user_id = $(this).data("user_id");
    let $modal = $("#modalDeleteUser");
    let $btn = $modal.find("#btnConfirm");
    let btnText = $btn.text();
  
    button_status($btn, "Excluindo...");
    
    $.ajax({
      url: `/admin/users/${user_id}/delete`,
      type: "POST",
      success: function(res) {
        button_status($btn, btnText, false);
        
        $modal.modal("hide");
        load_users();
        
        alertt("#alert", res.color, res.message);
      }
    });
  });
});
