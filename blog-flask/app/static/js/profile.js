$(document).ready(function() {
  let cropper;
  let imageToCrop;
  let croppedImagePreview;
  let uploadButton;
  let uploadDelete;
  let fileType;
  
  //FUNÇÃO PARA CARREGAR A PÁGINA DE DADOS PESSOAIS
  window.Profile = {
    load_profile_info: function() {
      $("#profile_info").find("#spinner").removeClass("d-none");
      $("#profile_info").find("#profile_data_content").addClass("d-none");
      
      $.ajax({
        url: '/profile/info',
        type: 'GET',
        success: function(html) {
          $("#profile_data_content").html(html);
          
          $("#profile_info").find("#profile_data_content").removeClass("d-none");
          $("#profile_info").find("#spinner").addClass("d-none");
        }
      });
    }
  };
  
  //FUNÇÃO PARA CARREGAR A PÁGINA DE FOTO DE PERFIL
  function load_profile_photo() {
    $("#profile_photo").find("#spinner").removeClass("d-none");
    $("#profile_photo").find("#profile_photo_content").addClass("d-none");
    
    $.ajax({
      url: '/profile/photo/view',
      type: 'GET',
      success: function(html) {
        $("#profile_photo_content").html(html);
        $("#profile_photo").find("#profile_photo_content").removeClass("d-none");
        $("#profile_photo").find("#spinner").addClass("d-none");
        
        imageToCrop = window.document.getElementById("imageToCrop");
        croppedImagePreview = window.document.getElementById("croppedImagePreview");
        uploadButton = window.document.getElementById("uploadButton");
        uploadDelete = window.document.getElementById("deletePreviewButton");
      }
    });
  }
  
  //CARREGA A PÁGINA DADOS PESSOAIS E FOTO DE PERFIL
  Profile.load_profile_info();
  load_profile_photo();
  
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
        }
        
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
  }).on("hidden.bs.modal", function() {
    if (cropper) {
      cropper.destroy();
      cropper = null;
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
        filename = "cropped_image.jpg"
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
        load_profile_photo();
        
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
        load_profile_photo();
        
        setTimeout(() => {
          alertt("#photo_message", res.color, res.message);
        }, 50);
      }
    });
  });
});