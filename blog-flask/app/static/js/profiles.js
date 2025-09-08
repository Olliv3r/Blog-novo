$(document).ready(function() {
//   let cropper;
//   let imageToCrop;
//   let croppedImagePreview;
//   let uploadButton;
//   let uploadDelete;
  let fileType;
  
  //FUNÇÃO PRA CARREGAR LISTA USUÁRIOS NO PAINEL ADMIN
  function load_profiles() {
    let $profiles = $("#profiles");
    
    $.ajax({
      url: "/admin/profiles/render",
      type: "GET",
      success: function(html) {
        $profiles.html(html);
        
        $profiles.find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }
  function load_social_medias(profile_id) {
    let $social = $("#social");
    
    $.ajax({
      url: `/admin/users/profiles/${profile_id}/social-medias/render`,
      type: "GET",
      success: function(html) {
        $social.html(html);
        
        $social.find(".created").each(function() {
          let dataText = $(this).text();
          let formattedText = formatData(dataText);
          
          $(this).text(formattedText);
        });
      }
    });
  }
  
  //CARREGA TODOS OS PERFIS POR PADRÃO
  load_profiles();
  
  /*
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
  */
  
  // FUNÇÃO PARA MONTAR UM SELECT
  function populateSelect(selectId, data, defaultId = null, includeEmptyOption = false) {
      const select = $(selectId).empty();
      
      // Mostra a opção fantasma
      if (includeEmptyOption) {
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
      
      if (defaultId !== null) {
          select.val(defaultId);
      }
  }
  
  // PREENCHE UM FORMULÁRIO COM SUPORTE PARA IMAGENS
  function fillFormFields(formSelector, data) {
      Object.entries(data).forEach(([key, value]) => {
          const $el = $(`${formSelector} #${key}`);
          
          if (!$el.length) return;
          
          // Verifica se é um campo de checkbox
          if ($el.is(":checkbox")) {
              $el.prop("checked", !!value);
          } 
          // Verifica se é um campo de imagem (img tag)
          else if ($el.is("img")) {
              $el.attr("src", value || "/default-image.jpg");
              // Opcional: armazenar o valor original em data attribute
              $el.data("original-src", value);
          }
          // Verifica se é um input file (para preview)
          else if ($el.is(":file")) {
              // Para inputs file, normalmente não preenchemos o value por segurança
              // Mas podemos mostrar um preview se houver uma URL de imagem
              const previewId = $el.data("preview");
              if (previewId && value) {
                  $(previewId).attr("src", value).show();
              }
          }
          // Verifica se é um textarea
          else if ($el.is("textarea")) {
              $el.text(value || "");
          }
          // Para todos os outros inputs (text, email, number, etc.)
          else {
              $el.val(value || "");
          }
      });
  }
  
  /*
  Pega o id do perfil e guarda no atributo 'profile_id' da
    modal 'modalEditProfile'
  */
  $("#profiles").on("click", "[data-edit-profile-id]", function() {
    let profile_id = $(this).data("edit-profile-id");
    $("#modalEditProfile").data("profile_id", profile_id);
  });
  
  // Preenche dados pessoais, email, url da foto e redes sociais por padrão
  $("#modalEditProfile").on("shown.bs.modal", function() {
    $modal = $(this);
    let profile_id = $modal.data("profile_id");
    
    $.ajax({
      url: `/admin/users/profiles/${profile_id}/data`,
      type: "GET",
      success: function(data) {
        const user = data.user;
        const profile = data.profile;
        const social_medias = data.social_medias;
        
        // Preenche dados pessoais
        fillFormFields("#formEditInfo", profile);
        
        // Preenche o email atual
        $("#formEditEmail").find("#email").val(user.email);
        
        // BOTÃO SALVAR
        $("#formEditPhoto #submitPhoto").prop("disabled", true);
        
        // BOTÃO DELETAR
        const hasCustomImage = profile.image_url ? true : false;
        $("#formEditPhoto #deletePhoto").prop("disabled", !hasCustomImage);
        
        updateButtonAppearance();
        
        // Carrega imagem, url da imagem ou avatar
        $("#formEditPhoto").find("#croppedImagePreview").attr("src", profile.image_url ? profile.image_url : user.avatar);
        /*
        Guarda url da imagem pra restaurar quando cancelar
          selecão da imagem
        */
        $("#formEditPhoto").find("#currentImageUrl").attr("src", profile.image_url ? profile.image_url : user.avatar);
        
        $("#formEditPhoto").find("#image_url").val(profile.image_url || "");
        
        // Carrega lista de redes sociais de um perfil
        load_social_medias(profile_id);
        
        setTimeout(function() {
          updateButtonStates();
        }, 100);
      }
    });
  });
  
  function updateButtonStates() {
    // Verifica se há imagem customizada (não é avatar padrão)
    const currentImageSrc = $("#currentImageUrl").attr("src") || "";
    const isDefaultAvatar = currentImageSrc.includes("avatar") || currentImageSrc.includes("default") || currentImageSrc.includes("gravatar") || currentImageSrc ==='';
    
    const hasCustomImage = !isDefaultAvatar && currentImageSrc !== '';
    
    // Verificar se há algo para salvar - IGNORANDO O AVATAR
    const hasFile = $("#imageUpload").val() !== '';
    const urlValue = $("#image_url").val().trim();
    
    const isAvatarUrl = urlValue.includes('gravatar.com') || urlValue.includes('avatar/') || urlValue.match(/[0-9a-f]{32}/);
    
    const hasReadUrl = urlValue !== '' && !isAvatarUrl;
    const isValidUrl = hasReadUrl ? urlValue.startsWith('http') : false;

    // BOTÃO DELETAR - só ativa se tem imagem customizada
    $("#formEditPhoto #deletePhoto").prop("disabled", !hasCustomImage);
    
    // BOTÃO SALVAR - ativo se tem arquivo OU URL válida
    $("#formEditPhoto #submitPhoto").prop("disabled", !(hasFile || isValidUrl));
    
    // BOTÃO CANCELAR - ativo apenas se tem arquivo selecionado
    $("#formEditPhoto #cancelPhoto").prop("disabled", !hasFile);
    
    updateButtonAppearance();
    
    console.log('updateButtonStates - currentImageSrc:', currentImageSrc);
    console.log('updateButtonStates - isDefaultAvatar:', isDefaultAvatar);
    console.log('updateButtonStates - hasCustomImage:', hasCustomImage);
    console.log('updateButtonStates - deleteButton disabled:', !hasCustomImage);
  }
  
  function updateButtonAppearance() {
    // Botão DELETAR
    const saveBtn = $("#formEditPhoto #submitPhoto");
    const deleteBtn = $("#formEditPhoto #deletePhoto");
    const cancelBtn = $("#formEditPhoto #cancelPhoto");
    
    // Botão SALVAR
    if (saveBtn.prop("disabled")) {
      saveBtn.removeClass("btn-success").addClass("btn-secondary");
    } else {
      saveBtn.removeClass("btn-secondary").addClass("btn-success");
    }
    
    // Botão DELETAR
    if (deleteBtn.prop("disabled")) {
      deleteBtn.removeClass("btn-danger").addClass("btn-secondary");
    } else {
      deleteBtn.removeClass("btn-secondary").addClass("btn-danger");
    }
    
    // Botão CANCELAR
    if (cancelBtn.prop("disabled")) {
      cancelBtn.removeClass("btn-warning").addClass("btn-secondary");
    } else {
      cancelBtn.removeClass("btn-secondary").addClass("btn-warning");
    }
    
    // Opacidade para todos os botões desabilitados
    $("button:disabled").css("opacity", "0.6");
    $("button:not(:disabled").css("opacity", "1");
  }
  
  // Monitora mudança no input de arquivo
  $("#imageUpload").on("change", function() {
    updateButtonStates();
  });
  
  // Monitora digitação no campo de URL
  $("#image_url").on("input", function() {
    updateButtonStates();
    
    // Validação visual da URL
    const url = $(this).val().trim();
    
    if (url !== '' && !url.startsWith('http')) {
      $(this).addClass("is-invalid");
    } else {
      $(this).removeClass("is-invalid");
    }
  });
  
  $("#cancelPhoto").on("click", function() {
    let current_image_url = $("#currentImageUrl")[0]["currentSrc"];
    $("#imageUpload").val("");
    $("#croppedImagePreview").attr("src", current_image_url);
    
    updateButtonStates();
  });
  
  // ABRIR SELEÇÃO DE IMAGEM AO CLICAR NA IMAGEM ATUAL
  $("#formEditPhoto").on("click", "#croppedImagePreview", function() {
    $("#imageUpload").click();
  });
  
  // QUANDO UMA NOVA IMAGEM É SELECIONADA
  $("#formEditPhoto").on("change", "#imageUpload", function(event) {
    let files = event.target.files;
    
    if (files.length > 0) {
      let file = files[0];
      let fileType = file.type;
      
      // Verificar se é uma imagem JPEG ou PNG
      if (fileType === "image/jpeg" || fileType === "image/png" || fileType === "image/jpg") {
        let reader = new FileReader();
        
        reader.onload = function(e) {
          // ATUALIZA DIRETAMENTE A IMAGEM ATUAL
          $("#croppedImagePreview").attr("src", e.target.result);
          // Opcional: Mostrar mensagem de sucesso
          alertt("#sub-alert", "success", "Imagem selecionada com sucesso!");
          $("#formEditPhoto #cancelPhoto").prop("disabled", false);
        };
        
        reader.readAsDataURL(file);
      } else {
        // Tipo de arquivo inválido
        alertt("danger", "Por favor, selecione um arquivo de imagem JPEG ou PNG.");
        $(this).val(""); // Limpa o input
        $("#formEditPhoto #cancelPhoto").prop("disabled", true);
      }
    }
  });
  
  // SUBMIT DO FORMULÁRIO DE FOTO
  $(document).on("submit", "#formEditPhoto", function(e) {
    e.preventDefault();
    if ($("#submitPhoto").prop("disabled")) {
      alertt("#sub-alert", "warning", "Selecione uma imagem ou informe uma URL válida");
      return false;
    }
    
    // Enviar o formulário
    submitPhotoForm(this);
  });
   
  // FUNÇÃO para enviar o formulário 
  function submitPhotoForm(form) {
    let profile_id = $("#modalEditProfile").data("profile_id");
    const formData = new FormData(form);

    formData.append("profile_id", profile_id);
    
    $.ajax({
      url: "/admin/users/profiles/update-photo",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      beforeSend: function() {
        $("#formEditPhoto #submitPhoto").prop("disabled", true)
          .html('<i class="fas fa-spinner fa-spin"></i> Salvando...');
      },
      success: function(response) {
        if (response.status === "success") {
          // Atualiza a imagem atual
          $("#croppedImagePreview").attr("src", response.new_image_url);
          $("#currentImageUrl").attr("src", response.new_image_url);
          $("#image_url").val(response.image_url || "");
          
          // Limpa o upload e atualiza os botões
          $("#imageUpload").val("");
          updateButtonStates();
          
          // Recarrega os cards de perfis
          setTimeout(function() {
            load_profiles();
          }, 30);
        }
        
        alertt("#sub-alert", response.color, response.message);
      },
      complete: function() {
        $("#formEditPhoto #submitPhoto").prop("disabled", false)
          .html('<i class="fas fa-save"></i> Salvar');
      }
    });
  };
  
  // BOTÃO PARA EXCLUIR FOTO
  $(document).on("click", "#formEditPhoto #deletePhoto", function() {
    const profile_id = $("#modalEditProfile").data("profile_id");
    
    $.ajax({
      url: "/admin/users/profiles/delete-photo",
      type: "POST",
      data: { profile_id: profile_id },
      beforeSend: function() {
        $("#formEditPhoto #deletePhoto").prop("disabled", true).html('<i class="fas fa-spinner fa-spin"></i> Excluindo...');
      },
      success: function(response) {
        console.log('Botão delete existe?', $("#formEditPhoto #deletePhoto").length > 0);
        console.log('Botão delete disabled?', $("#formEditPhoto #deletePhoto").prop('disabled'));
        
        if (response.status === "success") {
          // Atualiza para avatar padrão
          $("#croppedImagePreview").attr("src", response.new_image_url);
          $("#currentImageUrl").attr("src", response.new_image_url);
          $("#image_url").val(response.new_image_url);
          $("#imageUpload").val("");

          // Atualiza os botões
          setTimeout(function() {
            updateButtonStates();
            console.log("botões atualizados.")
          }, 150);
          
          // Recarrega os cards de perfis
          setTimeout(function() {
            load_profiles();
          }, 30);
        }
        
        alertt("#sub-alert", response.color, response.message);
      },
      complete: function() {
        $("#formEditPhoto #deletePhoto").prop("disabled", false)
          .html('<i class="fas fa-trash"></i> Excluir');
      }
    });
  });
 
 
  
  //CARREGAR AS SITUAÇÔES DE USUÁRIOS
  /*
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
  */
});
