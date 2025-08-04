$(document).ready(function() {
  let maxAttemps = 200;
  let attemps = 0;
  
  //FUNÇÃO PARA CARREGAR A PÁGINA DE SENHA NO PERFIL DO USUÁRIO
  function load_profile_password() {
    $("#profile_password").find("#spinner").removeClass("d-none");
    $("#profile_password").find("#profile_password_content").addClass("d-none");
    
    $.ajax({
      url: '/auth/profile/password/view',
      type: 'GET',
      success: function(html) {
        $("#profile_password_content").html(html);
        $("#profile_password").find("#profile_password_content").removeClass("d-none");
        $("#profile_password").find("#spinner").addClass("d-none");
      }
    });
  }
  
  //ESCONDE O MINI-MENU(OPÇÔES E EDITAR), MOSTRA O FORMULARIO DO E-MAIL E ESCONDE A AJUDA
  $("#profile_info").on("click", "#btn-edit-email", function() {
    $("#container_current_email").hide();
    $("#group_new_email").show();
    $("#emailHelp").hide();
  });
  
  //MOSTRA O MINI-MENU(OPÇÔES e EDITAR), ESCONDE O FORMULARIO DO E-MAIL E MOSTRA A AJUDA
  $("#profile_info").on("click", "#btn-email-close", function() {
    $("#container_current_email").show();
    $("#group_new_email").hide();
    $("#emailHelp").show();
  });
  
  //FUNÇÃO PARA VERIFICAR A VALIDADE DO TOKEN DE ATUALIZAÇÃO DO E-MAIL
  function check_validate_token_email() {
    attemps++;
    
    $.ajax({
      url: "/auth/profile/check-token-email",
      type: "POST",
      success: function(res) {
        //INTERROMPE a verificação se exceder o limite de 10m
        if (attemps >= maxAttemps) {
          console.warn("Tempo limite atingido. Token expirado?");
          $("#profile_info").find("#btn-email-resend").prop("disabled", false);
          clearInterval(window.checkTokenEmailSetInterv);
          alertt("#info_message", "warning", "O tempo de confirmação expirou. Reenvie o e-eail.");
        }
        
        //Se o Token for invalido ou expirado, INTERROMPE a verificação e ativa o button
        if(!res.is_valid) {
          Profile.load_profile_info();
          
          setTimeout(() => {
            $("#profile_info").find("#btn-email-resend").prop("disabled", false);
          }, 50);
          
          clearInterval(window.checkTokenEmailSetInterv);
        }
      },
      error: function() {
        console.error("Erro na verificação do token");
      }
    });
  }
  
  //VERIFICA VALIDADE DO TOKEN DE ATUALIZAÇÃO DO E-MAIL POR PADRÃO
  check_validate_token_email();
  
  //ENVIA UMA SOLICITAÇÃO DE ATUALIZAÇÃO DO E-MAIL
  $("#profile_info").on("click", "#btn-confirm-email", function() {
    var email = $("#group_new_email").find("#email").val();
    
    sendConfirmationEmail(email);
    
    $("#container_current_email").show();
    $("#group_new_email").hide();
    $("#emailHelp").show();
    
    if (window.checkTokenEmailSetInterv) {
      clearInterval(window.checkTokenEmailSetInterv);
    }
    
    window.checkTokenEmailSetInterv = setInterval(check_validate_token_email, 3000);
  });

  //REINVIAR UMA SOLICITAÇÃO DE ALTERAÇÃO DO E-MAIL
  $("#profile_info").on("click", "#btn-email-resend", function() {
    var new_email = $(this).data("email");
    
    sendConfirmationEmail(new_email);
  });
  
  //FUNÇÃO PRA ENVIAR UMA SOLICITAÇÃO DE ATUALIZAÇÃO DO E-MAIL
  function sendConfirmationEmail(email) {
    $.ajax({
      url: "/auth/profile/email/change",
      type: "POST",
      data: {new_email: email},
      success: function(res) {
        Profile.load_profile_info();
        
        setTimeout(() => {
          alertt("#email_message", res.color, res.message);
        }, 50);
      }
    });
    
    if (window.checkTokenEmailSetInterv) {
      clearInterval(window.checkTokenEmailSetInterv);
    }
    
    window.checkTokenEmailSetInterv = setInterval(check_validate_token_email, 3000);
  }
  
  //CANCELA A SOLICITAÇÃO DE ATUALIZAÇÃO DO EMAIL
  $("#profile_info").on("click", "#btn-email-cancel", function() {
    $.ajax({
      url: "/auth/profile/email/cancel",
      type: "POST",
      success: function(res) {
        if (window.checkTokenEmailSetInterv) {
          clearInterval(window.checkTokenEmailSetInterv);
        }
        
        Profile.load_profile_info();
        
        setTimeout(() => {
          alertt("#info_message", res.color, res.message);
        }, 50);
      }
    });
  });
  
  //CARREGA FORMULARIO DE SENHA
  load_profile_password();
  
  $("#profile_password").on("submit", "#FormPassword", function(e) {
    e.preventDefault();
    
    button_status($(this).find("#btn-edit"), "Aguarde...");
    
    if($(this).find("#password").val() !== $(this).find("#password2").val()) {
      load_profile_password();
      
      setTimeout(() => {
        alertt("#password_message", "danger", "As senhas não conferem!");
      }, 50);
      return;
    }
    
    if ($(this).find("#password").val().length < 6 || $(this).find("#password2").val().length < 6) {
      load_profile_password();
      
      setTimeout(() => {
        alertt("#password_message", "danger", "Tamanho mínimo da senha é 6 caracteres!");
      }, 50);
      return;
    }
    
    let formData = new FormData(this);
    let user_id = $(this).data("form-id");
  
    formData.append("user_id", user_id);
    
    $.ajax({
      url: "/auth/profile/password",
      type: "POST",
      data: formData,
      processData: false,
      contentType: false,
      success: function(res) {
        load_profile_password();
        
        setTimeout(() => {
          alertt("#password_message", res.color, res.message);
        }, 50);
      }
    });
  });
});