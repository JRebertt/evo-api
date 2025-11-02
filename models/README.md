# Pasta de Fotos de Modelos

## 📸 Como Adicionar Fotos

Coloque as fotos das modelos nesta pasta. O CLI selecionará automaticamente uma foto diferente para cada instância.

### Formatos Suportados
- JPG
- JPEG
- PNG

### Recomendações

1. **Qualidade**: Use fotos de boa qualidade (mínimo 500x500px)
2. **Formato**: Preferencialmente fotos quadradas ou verticais
3. **Tamanho**: Máximo 5MB por foto
4. **Quantidade**: Adicione várias fotos para ter variedade

### Exemplo de Estrutura

```
models/
├── modelo1.jpg
├── modelo2.jpg
├── modelo3.png
├── modelo4.jpg
└── ...
```

### ⚠️ Importante

- Cada instância usa uma foto **única**
- Se todas as fotos forem usadas, o CLI pedirá para adicionar mais
- Não use fotos de pessoas reais sem permissão
- Respeite direitos autorais e privacidade

### 🔄 Gerenciamento

O CLI automaticamente:
- ✅ Lista todas as fotos disponíveis
- ✅ Rastreia quais fotos já foram usadas
- ✅ Seleciona aleatoriamente uma foto não utilizada
- ✅ Alerta quando não há mais fotos disponíveis

### Adicionar Mais Fotos

Basta copiar novas fotos para esta pasta:

```bash
cp /caminho/das/novas/fotos/*.jpg models/
```

O CLI detectará automaticamente as novas fotos.
