# Evolution API CLI - Gerenciador de Instâncias com Personas

CLI interativo para gerenciar instâncias da Evolution API v2.3 com criação automática de personas femininas brasileiras usando Gemini AI.

## 📋 Funcionalidades

- ✅ Criação automática de instâncias
- ✅ Conexão WhatsApp com QR Code
- ✅ Detecção automática de conexão
- ✅ Geração de personas com Gemini AI
- ✅ Configuração automática de perfil (foto, nome, bio)
- ✅ Gerenciamento de fotos de modelos (sem repetição)
- ✅ Armazenamento de dados das instâncias

## 🚀 Instalação

### 1. Instalar dependências

```bash
pip3 install requests openai
```

### 2. Configurar API Keys

Edite o arquivo `config.json`:

```json
{
  "evolution_api": {
    "base_url": "http://localhost:8080",
    "global_apikey": "SUA_API_KEY_GLOBAL_AQUI"
  },
  "gemini": {
    "api_key": "SUA_API_KEY_GEMINI_AQUI",
    "model": "gemini-2.5-flash"
  }
}
```

**Nota:** A API key do Gemini deve ser configurada na variável de ambiente `OPENAI_API_KEY` (já está configurada no sandbox).

### 3. Adicionar fotos de modelos

Coloque fotos de modelos na pasta `models/`:

```bash
cp /caminho/das/fotos/*.jpg models/
```

**Formatos suportados:** JPG, JPEG, PNG

## 📖 Como Usar

### Iniciar o CLI

```bash
python3 cli.py
```

### Menu Principal

```
1. Criar nova instância e conectar
2. Listar instâncias
3. Configurar persona manualmente
4. Verificar status de conexão
5. Sair
```

### Fluxo Automático (Opção 1)

1. **Criar Instância**: Digite o nome da instância
2. **QR Code**: Será gerado automaticamente
3. **Conectar WhatsApp**: Escaneie o QR Code com seu WhatsApp
4. **Aguardar Conexão**: O CLI detecta automaticamente quando conectar
5. **Persona Automática**: Após conexão, a persona é criada e configurada automaticamente

### O que acontece automaticamente:

1. ✅ Seleciona foto aleatória (não repetida) da pasta `models/`
2. ✅ Gera persona com Gemini (nome, idade, cidade, profissão, bio, etc.)
3. ✅ Atualiza foto do perfil do WhatsApp
4. ✅ Atualiza nome do perfil
5. ✅ Atualiza bio do perfil
6. ✅ Salva todos os dados da persona

## 📁 Estrutura de Pastas

```
evolution-cli/
├── cli.py              # CLI principal
├── config.json         # Configurações
├── README.md          # Este arquivo
├── ai/
│   └── prompt.txt     # Prompt para geração de personas
├── models/            # Fotos de modelos (adicione aqui)
│   ├── modelo1.jpg
│   ├── modelo2.jpg
│   └── ...
└── data/              # Dados das instâncias (gerado automaticamente)
    ├── instances.json
    └── *_qr.txt
```

## 🎭 Características das Personas

Cada persona gerada possui:

- **Nome**: Nome e sobrenome brasileiros
- **Idade**: 20-30 anos
- **Cidade**: Cidades brasileiras
- **Profissão**: Profissões realistas
- **Hobbies**: 3-5 interesses
- **Bio**: Máximo 139 caracteres (otimizada para WhatsApp)
- **Estilo de conversa**: Tom descontraído, flertante, com gírias brasileiras
- **Personalidade**: Carente, sedutora, extrovertida

## 🔧 Configurações Avançadas

### Webhook (Opcional)

Para ativar webhook, edite `config.json`:

```json
"webhook": {
  "url": "https://seu-webhook.com/endpoint",
  "enabled": true
}
```

### Settings da Instância

Configure comportamento padrão em `config.json`:

```json
"settings": {
  "reject_call": false,
  "msg_call": "",
  "groups_ignore": true,
  "always_online": false,
  "read_messages": false,
  "read_status": false,
  "sync_full_history": false
}
```

## 📊 Arquivo de Dados

O arquivo `data/instances.json` armazena:

```json
{
  "nome_instancia": {
    "name": "nome_instancia",
    "apikey": "hash_da_instancia",
    "created_at": 1234567890,
    "connected": true,
    "model_photo": "modelo1.jpg",
    "persona": {
      "nome": "Maria Silva",
      "idade": 25,
      "cidade": "São Paulo",
      "profissao": "Designer Gráfica",
      "hobbies": ["viajar", "fotografia"],
      "bio": "Explorando a vida ✨",
      "estilo_conversa": "...",
      "personalidade": "..."
    }
  }
}
```

## 🎨 Personalizando Personas

Para ajustar o prompt das personas, edite `ai/prompt.txt`.

Você pode modificar:
- Características de personalidade
- Faixa etária
- Estilo de conversa
- Formato da bio
- Etc.

## ⚠️ Avisos Importantes

1. **Fotos Únicas**: Cada instância usa uma foto diferente. Se todas as fotos forem usadas, o CLI pedirá para adicionar mais.

2. **QR Code**: O QR Code expira após alguns minutos. Se não conectar a tempo, será necessário gerar um novo.

3. **Conexão**: O CLI aguarda até 120 segundos pela conexão. Se não conectar, você pode tentar novamente manualmente.

4. **API Keys**: Certifique-se de que as API keys estão corretas no `config.json`.

## 🐛 Troubleshooting

### Erro: "Arquivo config.json não encontrado"
- Certifique-se de estar executando o CLI na pasta correta

### Erro ao gerar persona
- Verifique se a API key do Gemini está configurada corretamente
- Verifique se a variável de ambiente `OPENAI_API_KEY` está definida

### Erro ao atualizar foto
- Verifique se a foto existe na pasta `models/`
- Certifique-se de que o formato é JPG, JPEG ou PNG

### Instância não conecta
- Verifique se a Evolution API está rodando
- Verifique se a URL base está correta no `config.json`
- Tente gerar um novo QR Code

## 📝 Próximos Passos

Após configurar a persona, você pode implementar:
- Resposta automática a mensagens
- Fluxo de conversa com IA
- Integração com outros serviços
- Etc.

## 📄 Licença

Este projeto é baseado na Evolution API v2.3 e utiliza Gemini AI para geração de personas.

## 🤝 Suporte

Para dúvidas ou problemas, consulte:
- [Documentação Evolution API](https://doc.evolution-api.com)
- [Postman Collection](https://www.postman.com/agenciadgcode/evolution-api)
