$(document).ready(function() {
  let cropper;
  let imageToCrop;
  let croppedImagePreview;
  let uploadButton;
  let uploadDelete;
  let fileType;
  
  window.Profile = {
    //FUNÇÃO PARA CARREGAR A PÁGINA DE DADOS PESSOAIS
    load_profile_info: function() {
      let $profile = $("#profile_info");
      let $content = $profile.find("#profile_data_content");
      let $spinner = $profile.find("#spinner");
      
      $spinner.removeClass("d-none");
      $content.addClass("d-none");
      
      $.ajax({
        url: '/profile/info',
        type: 'GET',
        success: function(html) {
          $content.html(html);
          $content.removeClass("d-none");
          $spinner.addClass("d-none");
        }
      });
    },
    
    //FUNÇÃO PARA CARREGAR A PÁGINA DE REDES SOCIAIS
    load_profile_social_media: function() {
      let $profile = $("#profile_sm");
      let $content = $profile.find("#profile_sm_content");
      let $spinner = $profile.find("#spinner");
      
      $spinner.removeClass("d-none");
      $content.addClass("d-none");
      
      $.ajax({
        url: '/profile/social-media',
        type: 'GET',
        success: function(html) {
          $content.html(html);
          $content.removeClass("d-none");
          $spinner.addClass("d-none");
          Profile.load_profile_list_sm();
        }
      });
    },
    
    //FUNÇÃO PARA CARREGAR LISTA DE REDES SOCIAIS NA PÁGINA REDES SOCIAIS
    load_profile_list_sm: function() {
      let $profile = $("#profile_sm");
      let $content = $profile.find("#profile_list_sm");
      
      $.ajax({
        url: '/profile/social-media/render',
        type: 'GET',
        success: function(html) {
          $content.html(html);
          initiateSortable();
        }
      });
    },
    
    //FUNÇÃO PARA CARREGAR A PÁGINA DE FOTO DE PERFIL
    load_profile_photo: function() {
      let $profile = $("#profile_photo");
      let $content = $profile.find("#profile_photo_content");
      let $spinner = $profile.find("#spinner");
      
      $spinner.removeClass("d-none");
      $content.addClass("d-none");
      
      $.ajax({
        url: '/profile/photo/view',
        type: 'GET',
        success: function(html) {
          $content.html(html);
          $content.removeClass("d-none");
          $spinner.addClass("d-none");
          
          imageToCrop = window.document.getElementById("imageToCrop");
          croppedImagePreview = window.document.getElementById("croppedImagePreview");
          uploadButton = window.document.getElementById("uploadButton");
          uploadDelete = window.document.getElementById("deletePreviewButton");
        }
      });
    }
  };

  //CARREGA A PÁGINA DADOS PESSOAIS, REDES SOCIAIS E FOTO DE PERFIL
  Profile.load_profile_info();
  Profile.load_profile_social_media();
  Profile.load_profile_photo();
  
  //EDITA DADOS PESSOAIS DO USUÁRIO
  $("#profile_info").on("submit", "#edit_info", function(e) {
    e.preventDefault();
    
    user_id = $(this).data("edit-info-id");
    formData = new FormData(this);
    
    formData.append("user_id", user_id);
    btn = $(this).find("#btn_edit_info");
    
    button_status(btn, "Processando...");
    
    $.ajax({
      url: "/profile/edit/info",
      type: "POST",
      data: formData,
      contentType: false,
      processData: false,
      success: function(res) {
        Profile.load_profile_info();
        
        setTimeout(() => {
          alertt("#info_message", res.color, res.message);
        }, 50);
      }
    });
  });
  
  // Mostra o form de cadastro da rede social - BN
  $("#profile_sm_content").on("click", ".form-add-sm", function(e) {
    e.preventDefault();
    let targetForm = $("#addFormSm");
    
    $(targetForm).toggle();
    
    $(this).toggleClass("disabled");
    $(".btn-view-form-sm").toggleClass("disabled");
    $(".btn-edit-form-sm").toggleClass("disabled");
    $(".btn-delete-form-sm").toggleClass("disabled");
    
    $("html, body").animate({
      scrollTop: $(".form-add-sm").offset().top - 50
    }, 1000);
  });
  
  // Esconder o form de cadastro da rede social - BN
  $("#profile_sm_content").on("click", ".form-cancel-button", function(e) {
    e.preventDefault();
    
    let targetForm = $("#addFormSm");
    
    $(targetForm).hide();
    $(".form-add-sm").removeClass("disabled");
    $(".btn-view-form-sm").removeClass("disabled");
    $(".btn-edit-form-sm").removeClass("disabled");
    $(".btn-delete-form-sm").removeClass("disabled");
    
    $("html, body").animate({
      scrollTop: $(".form-add-sm").offset().top - 50
    }, 1000);
  });
  
  // Cadastrar uma rede social
  $("#profile_sm_content").on("submit", "#addFormSm", function(e) {
    e.preventDefault();
    
    let $form = $(this);
    let $btn = $form.find(".form-add-button");
    let btnText = $btn.text();
    let formData = $form.serialize();
    
    button_status($btn, "Adicionando...");
    
    $.ajax({
      url: $form.attr("action"),
      type: "POST",
      data: formData,
      success: function(response) {
        $form[0].reset();
        $form.hide();
        button_status($btn, btnText, false);
        
        if(response.status === "success") {
          Profile.load_profile_list_sm();
        }
  
        alertt("#alert", response.color, response.message);
        
        $(".form-add-sm").removeClass("disabled");
        $(".btn-view-form-sm").removeClass("disabled");
        $(".btn-edit-form-sm").removeClass("disabled");
        $(".btn-delete-form-sm").removeClass("disabled");
        
        $("html, body").animate({
          scrollTop: $(".form-add-sm").offset().top - 50
        }, 1000);
      }
    });
  });
  
  // Mostra o form de edição da rede social - BN
  $("#profile_sm_content").on("click", ".btn-edit-form-sm", function(e) {
    e.preventDefault();
    let sm_id = $(this).data("sm-id");
    let targetForm = $("#editFormSm" + sm_id);
    
    $(targetForm).toggle();
    $(this).toggleClass("disabled");
    $(".form-add-sm").toggleClass("disabled");
    $(".btn-view-form-sm").toggleClass("disabled");
    $(".btn-edit-form-sm").toggleClass("disabled");
    $(".btn-delete-form-sm").toggleClass("disabled");
    
    if ($(targetForm).is(":visible")) {
      $(this).addClass("disabled");
      $(this).attr("href", "#");
      
    } else {
      $(this).removeClass("disabled");
      $(this).attr("href", "#");
    }
    
    $("html, body").animate({
      scrollTop: $(".form-add-sm").offset().top - 50
    }, 1000);
  });
  
  // Esconder formulário de edição ou exclusão das redes sociais
  $("#profile_sm_content").on("click", ".btn-cancel-form-sm", function() {
    var sm_id = $(this).data("sm-id");
    var targetForm = $("#editFormSm" + sm_id);
    
    $(targetForm).hide();
    
    $('.form-add-sm').removeClass("disabled");
    $(".btn-view-form-sm").removeClass("disabled");
    $(".btn-edit-form-sm").removeClass("disabled");
    $(".btn-delete-form-sm").removeClass("disabled");
    
    $("html, body").animate({
      scrollTop: $(".form-add-sm").offset().top - 50
    }, 1000)
  });
  
  // Editar rede social
  $("#profile_sm_content").on("submit", ".editFormSm", function(e) {
    e.preventDefault();
    
    let $form = $(this);
    let $btn = $form.find(".btn-confirm-form-sm");
    let btnText = $btn.text();
    let formData = $form.serialize();
    
    button_status($btn, "Atualizando...")
    
    $.ajax({
      url: $form.attr("action"),
      type: "POST",
      data: formData,
      success: function(response) {
        button_status($btn, btnText, false)
        
        if(response.status === "success") {
          Profile.load_profile_list_sm();
        }
        
        alertt("#alert", response.color, response.message);
        
        $(".form-add-sm").removeClass("disabled");
        
        $("html, body").animate({
          scrollTop: $(".form-add-sm").offset().top - 50
        }, 1000);
      }
    });
  });
  
  // Excluir uma rede social
  $("#profile_sm_content").on("click", ".btn-delete-modal-sm", function() {
    let sm_id = $(this).data("delete-sm-id");
    let modal = $("#deleteSmModal" + sm_id);
    
    let $btn = $(this);
    let btnText = $btn.text();
    
    button_status($btn, "Excluindo...")
    
    $.ajax({
      url: `/profile/social-media/${sm_id}/delete`,
      type: "POST",
      success: function(res) {
        $(modal).modal("hide");
        button_status($btn, btnText, false);
        
        if(res.status === "success") {
          $(modal).on("hidden.bs.modal", function() {
            Profile.load_profile_list_sm();
          });
          $(modal).modal("hide");
        }
        
        alertt("#alert", res.color, res.message);
        
        $("html, body").animate({
          scrollTop: $(".form-add-sm").offset().top - 50
        }, 1000);
      }
    })
  });
  
  // Atualizar status da rede social
  $("#profile_sm_content").on("change", ".sit_sm", function() {
    var sm_id = $(this).data("sit-sm-id");
    var is_active = $(this).is(":checked");
  
    $.ajax({
      url: `/profile/social-media/status/${sm_id}/update`,
      type: "POST",
      data: { sit_sm: is_active },
      success: function(res) {
        Profile.load_profile_list_sm();
        alertt("#alert", res.color, res.message);
      }
    });
  });
  
  // Mudar a ordem das redes sociais
  function initiateSortable() {
    var list = $("#social_media")[0];
    
    var sortable = new Sortable(list, {
      handle: '.position-sm',
      animation: 150,
      onEnd: function(evt) {
      	var items = $("#social_media .item-sm").toArray();
      	var newOrder = items.map(function(item, index) {
      	  return {
      	    id: $(item).data("order-sm-id"),
      	    order: index
      	  }
      	});
      	
      	$.ajax({
      	  url: `/profile/social-media/order/update`,
      	  type: "POST",
      	  contentType: "application/json",
      	  data: JSON.stringify({ order: newOrder }),
      	  success: function(res) {
      	    Profile.load_profile_list_sm();
      	    alertt("#alert", res.color, res.message);
      	  }
      	});
      }
    });
  }
  
  //ABRIR A GALERIA DE FOTOS PRA SELEÇÃ0
  $("#profile_photo").on("click", "#card_image", function() {
    $("#uploadImage").click();
  });
  
  //SELECIONA A FOTO
  $("#profile_photo").on("change", "#uploadImage", function(event) {
    let files = event.target.files;
    
    var done = function(url) {
      imageToCrop.src = url;
      $("#cropModal").modal("show");
    };
    
    if (files.length > 0) {
      let file = files[0];
      fileType = file.type;
      
      if(fileType === "image/jpeg" || fileType === "image/png") {
        let reader = new FileReader();
        
        reader.onload = function(e) {
          done(reader.result);
        };
        
        reader.readAsDataURL(files[0]);
      } else {
        alertt("#photo_message", "danger", "Por favor, selecione um arquivo de imagem JPEG ou PNG.");
        $(this).val("");
        
        if (cropper) {
          cropper.destroy();
          cropper = null;
        }
      }
    }
  });
  
  //ABRE O RECORTE DA FOTO
  $("#cropModal").on("shown.bs.modal", function() {
    cropper = new Cropper(imageToCrop, {
      aspectRatio: 1,
      viewMode: 3
    });
  }).on("hidden.bs.modal", function() {
    if (cropper) {
      cropper.destroy();
      cropper = null;
    }
  });
  
  //RECORTAR A FOTO
  $("#cropButton").on("click", function() {
    let canvas = cropper.getCroppedCanvas({
      width: 250,
      height: 250
    });
    
    let croppedImage = canvas.toDataURL("image/png");
    
    croppedImagePreview.src = croppedImage;
    $(croppedImagePreview).css("display", "block");
    $(uploadButton).prop("disabled", false);
    $(deletePreviewButton).prop("disabled", true);
    
    
    canvas.toBlob(function(blob) {
      let filename = "cropped_image.png";
      
      if (fileType == "image/jpeg") {
        filename = "cropped_image.jpg";
      } else if (fileType == "image/png") {
        filename = "cropped_image.png";
      }
      
      uploadButton.blob = new File([blob], filename, {type: blob.type}, fileType);
      
      $("#cropModal").modal("hide");
    });
  });
  
  //REQUISIÇÃO AJAX PRA SALVAR FOTO DE PERFIL NA BASE DE DADOS
  $("#profile_photo").on("click", "#uploadButton", function() {
    let button = $(this);
    let user_id = button.data("user-id");
    let formData = new FormData();
    
    button_status(button, "Aguarde");
    
    formData.append("user_id", user_id);
    formData.append("croppedImage", uploadButton.blob);
    
    $.ajax({
      url: "/profile/photo",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        Profile.load_profile_photo();
        
        setTimeout(() => {
          alertt("#photo_message", res.color, res.message);
        }, 50);
      }
    });
  });
  
  //Excluir foto de perfil
  $("#profile_photo").on("click", "#deletePreviewButton", function() {
    let user_id = $(this).data("user-id");
    let button = $(this);
    
    button_status(button, "Aguarde..");
    
    $.ajax({
      url: "/profile/photo/delete",
      type: "POST",
      data: {user_id: user_id},
      success: function(res) {
        Profile.load_profile_photo();
        
        setTimeout(() => {
          alertt("#photo_message", res.color, res.message);
        }, 50);
      }
    });
  });
});