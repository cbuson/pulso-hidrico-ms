# Pulso Hídrico MS · V0.8.6.3

Correção de distribuição **mobile first**.

## Mudanças

- No celular, P90, temperatura, máximo e trechos ativos ficam em um rail compacto ao lado direito do mapa.
- As fichas grandes de métricas continuam no layout de desktop, mas deixam de ocupar a parte inferior no celular.
- A tela principal `Pulso` usa quase toda a área disponível para o mapa; abaixo permanece apenas a linha temporal.
- `Camadas`, `Dados` e `Ajuda` continuam acessíveis pela barra inferior e abrem um painel inferior maior.
- Os botões de zoom foram movidos para a esquerda para não competir com o rail hidrológico.
- O enquadramento de Mato Grosso do Sul reserva espaço para o rail lateral no celular.
- A mensagem técnica longa sob o mapa é ocultada em telas estreitas; a metodologia permanece em `?` e `Ajuda`.
- Cache PWA atualizado para V0.8.6.3.

## Instalação

Copiar `docs/` sobre a versão existente, fazer commit/push e atualizar GitHub Pages. Nenhum dado GloFAS, DynQual ou GeoJSON é modificado.
