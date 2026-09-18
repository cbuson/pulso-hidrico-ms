# Pulso Hídrico MS · V0.9.2

Correção de navegação entre 2D/3D e de projetos relacionados.

## Alterações

- botão `2D` sempre visível no modo 3D, inclusive em telas abaixo de 390 px;
- botão `3D` preservado na interface 2D;
- ITA ARANDU MS com link público;
- PIH-MS incorporado como projeto relacionado, também com link público;
- referências em português e espanhol;
- reprodução automática permanece em 1,5 s por mês;
- cache PWA atualizado.

## Links

ITA ARANDU MS  
https://cbuson.github.io/atlas-geocientifico-ms/

PIH-MS  
https://cbuson.github.io/pih-ms/

## Instalação

Extraia o ZIP na raiz de `pulso-hidrico-ms` e execute:

```text
APLICAR_V0_9_2_FINAL.cmd
```

Depois:

```text
PRECHECK_V0_9_2.cmd
```

Teste:

```text
http://localhost:9564/
http://localhost:9564/3d/
```

A versão 2D deve mostrar `V0.9.2 · 2D + 3D`.
A versão 3D deve mostrar `V0.9.2 · MODO 3D`.
