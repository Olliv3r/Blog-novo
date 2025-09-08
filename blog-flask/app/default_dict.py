situations = [
  # Situações para papéis
  {"name": "Ativo", "description": "O papel está ativo e pode exercer suas permissões normalmente", "entity_type": "role"},
  {"name": "Inativo", "description": "O papel está inativo e não pode exercer suas permissões", "entity_type": "role"},
  {"name": "Suspenso", "description": "O papel está temporariamente suspenso e suas permissões estão restritas", "entity_type": "role"},
  {"name": "Pendente", "description": "O papel está pendente de aprovação ou revisão", "entity_type": "role"},

  # Situações para usuários
  {"name": "Ativo", "description": "Usuário pode acessar e utilizar todas as funcionalidades do sistema.", "entity_type": "user"},
  {"name": "Inativo", "description": "Usuário está desativado e não pode acessar o sistema.", "entity_type": "user"},
  {"name": "Aguardando", "description": "Usuário está aguardando aprovação para ativação ou ativação de sua conta.", "entity_type": "user"},
  {"name": "Suspenso", "description": "Usuário foi temporariamente suspenso e não pode acessar o sistema até a suspensão ser levantada.", "entity_type": "user"},

  # Situações para sugestôes
  {"name": "Publicada", "description": "Comentário está visível publicamente e pode ser visto por todos os usuários.", "entity_type": "suggestion"},
  {"name": "Aguardando", "description": "Comentário está aguardando moderação antes de ser publicado.", "entity_type": "suggestion"},
  {"name": "Removida", "description": "Comentário foi removido e não está mais visível para os usuários.", "entity_type": "suggestion"},

  # Situações para redes sociais
  {"name": "Ativo", "description": "A rede social está ativa e os links estão visíveis para os usuários.", "entity_type": "social_media"},
  {"name": "Inativo", "description": "A rede social está desativada e não aparece no perfil público.", "entity_type": "social_media"},
  {"name": "Aguardando", "description": "A rede social foi adicionada mas ainda aguarda verificação ou aprovação.", "entity_type": "social_media"},
  {"name": "Suspensa", "description": "A rede social foi temporariamente suspensa e não está acessível no momento.", "entity_type": "social_media"},
  {"name": "Removida", "description": "A rede social foi removida do perfil e não está mais disponível.", "entity_type": "social_media"}
]