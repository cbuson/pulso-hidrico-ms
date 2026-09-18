# Pulso Hídrico MS · V0.8.6.6

Correção da gráfica **Saída hídrica de MS**.

## O que foi corrigido

- quando a série de saída ainda não existe, a interface mostra `—` em vez de `0,000 m³/s`;
- a mensagem pública deixa de expor um comando local do Windows;
- `PREPARAR_SAIDA_HIDRICA_MS.cmd` instala/verifica `numpy` e `shapely`, valida os arquivos necessários e confirma os três arquivos gerados;
- `VALIDAR_GRAFICA_SAIDA.cmd` permite verificar antes do commit/push se a gráfica está realmente pronta para GitHub Pages;
- cache da PWA atualizado.

## Para ativar a gráfica online

1. Execute `PREPARAR_SAIDA_HIDRICA_MS.cmd` na raiz do projeto.
2. Confirme que existem:
   - `docs/data/outflow-ms.json`
   - `docs/data/outflow-ms.csv`
   - `docs/data/outflow-ms-outlets.geojson`
3. Opcionalmente execute `VALIDAR_GRAFICA_SAIDA.cmd`.
4. Faça commit e push **dos três arquivos**.
5. Aguarde a atualização do GitHub Pages e recarregue a PWA no celular.

A aplicação é estática no GitHub Pages. Ela pode ler `outflow-ms.json`, mas não pode executar Python no servidor para produzi-lo. Por isso a etapa de geração ocorre uma única vez no computador e o resultado processado é publicado em `docs/data`.
