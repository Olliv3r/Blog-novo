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

  # Situações para comentários
  {"name": "Publicado", "description": "Comentário está visível publicamente e pode ser visto por todos os usuários.", "entity_type": "comment"},
  {"name": "Aguardando", "description": "Comentário está aguardando moderação antes de ser publicado.", "entity_type": "comment"},
  {"name": "Removido", "description": "Comentário foi removido e não está mais visível para os usuários.", "entity_type": "comment"},

  # Situações para artigos
  {"name": "Rascunho", "description": "Artigo ainda está sendo escrito e não é visível publicamente.", "entity_type": "article"},
  {"name": "Publicado", "description": "Artigo foi publicado e está visível publicamente.", "entity_type": "article"},
  {"name": "Arquivado", "description": "Artigo foi arquivado e não está mais disponível publicamente.", "entity_type": "article"},
  {"name": "Aguardando revisão", "description": "Artigo está aguardando aprovação ou revisão editorial antes da publicação.", "entity_type": "article"}
]
block_types = [
    {"name": "Parágrafo", "description": "Texto corrido usado para desenvolvimento do conteúdo."},
    {"name": "Título", "description": "Título de uma seção ou parte do artigo."},
    {"name": "Subtítulo", "description": "Subseção para organizar melhor o conteúdo."},
    {"name": "Citação", "description": "Destaque para uma frase citada de outra fonte ou trecho importante."},
    {"name": "Código", "description": "Bloco para exibir trechos de código com formatação especial."},
    {"name": "Imagem", "description": "Inserção de uma imagem relevante para o artigo."},
    {"name": "Lista", "description": "Bloco contendo uma lista ordenada ou não."},
    {"name": "Aviso", "description": "Bloco visual para destacar avisos ou informações importantes."},
    {"name": "Separador", "description": "Uma linha ou espaçamento visual para separar seções."},
    {"name": "Tabela", "description": "Bloco para organizar dados em formato de tabela."}
]