# Pulso Hídrico MS — V0.8.4

Atualização de interface sobre a V8/V8.3. **Não altera nem apaga os dados já processados.**

## Mudanças

- reprodução automática passa a avançar **mês a mês**;
- consulta manual continua **diária** pelas setas, calendário e linha do tempo;
- o reprodutor tenta manter o mesmo dia do mês e usa a data disponível mais próxima quando necessário;
- botão **?** no cabeçalho com explicação do sistema, funcionamento, limites e links para as fontes;
- botão **i** no cabeçalho com autoria, instalação PWA, uso local, versão e licenças;
- autoria visível: **Carlos Busón Buesa** e **Sandra Gabas**;
- temperatura em modo Real fica explicitamente como **não incorporada**, sem valor sintético nem barra cromática enganosa;
- cache PWA atualizado para `pulso-hidrico-ms-v8.4`.

## Aplicação

Descompacte o ZIP **sobre a pasta atual** `pulso-hidrico-ms` e aceite substituir apenas os arquivos de `docs/` incluídos nesta atualização.

A atualização não contém `data/processed/`, `docs/data/pulse-v8/` nem os NetCDF. Portanto, a série GloFAS que já foi construída permanece intacta.

Depois execute:

`SERVIDOR_9564.cmd`

Abra `http://localhost:9564` e faça uma recarga forte na primeira vez (`Ctrl + Shift + R`). Se o navegador insistir na versão anterior, remova o Service Worker antigo em DevTools > Application > Service Workers > Unregister e recarregue.

## Reprodução mensal

Ao pressionar **Reproduzir · mensal**, a aplicação avança um mês por vez. A consulta individual de cada dia permanece disponível. Isso reduz a velocidade excessiva de uma animação diária de 25 anos sem retirar a resolução diária dos dados.

## Temperatura

A V0.8.4 não cria nem simula temperatura no modo Real. O painel mostra `—` e informa que a climatologia/temperatura ainda não foi incorporada. A futura integração deve entrar como uma fonte separada e documentada.
