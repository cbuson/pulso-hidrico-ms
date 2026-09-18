# Pulso Hídrico MS · V0.9.1 · 2D + 3D

Versão pública integrada preparada para GitHub Pages.

## Navegação

- **2D** é a interface científica principal.
- **3D** é uma visualização opcional dos rios com volume visual.
- o cabeçalho 2D contém um botão `3D`;
- a visualização 3D contém um botão `2D` para voltar.

## Velocidade de reprodução

A reprodução automática foi calibrada para a cadência observada no vídeo de referência de mapped.earth enviado durante o desenvolvimento.

O vídeo de referência tem 30 s e avança aproximadamente 20 dias por segundo. Isso equivale aproximadamente a:

- **1 mês a cada 1,5 s**
- **1 ano em cerca de 18 s**

Pulso Hídrico MS mantém a decisão metodológica anterior:

- consulta manual = **diária**;
- reprodução automática = **mensal**;
- intervalo automático = **1,5 s por mês**.

Assim a animação tem uma velocidade visual próxima da referência sem carregar 30 quadros diários por segundo nem comprometer a leitura científica.

## 3D

- terreno = DEM;
- largura dos rios = descarga GloFAS;
- altura visual dos rios = descarga GloFAS com transformação logarítmica fixa;
- cor = climatologia mensal DynQual;
- altura = codificação visual, não altitude física nem volume armazenado.

## Instalação

1. Faça uma cópia de segurança.
2. Extraia este ZIP na raiz de `pulso-hidrico-ms`.
3. Confirme a substituição de `docs/3d/`.
4. Execute:

```text
APLICAR_V0_9_1_FINAL.cmd
```

5. Execute:

```text
PRECHECK_V0_9_1.cmd
```

6. Inicie o servidor habitual e teste:

```text
http://localhost:9564/
http://localhost:9564/3d/
```

## Publicação

No GitHub Desktop, revise o commit antes do push.

Não publicar:
- `.cdsapirc`;
- tokens ou chaves;
- NetCDF brutos;
- `data/raw`;
- credenciais Copernicus.

Commit sugerido:

```text
Pulso Hídrico MS v0.9.1 - integração 2D + 3D e velocidade final
```

Depois de `Push origin`:

```text
https://cbuson.github.io/pulso-hidrico-ms/
https://cbuson.github.io/pulso-hidrico-ms/3d/
```

## Preflight

- 2D abre normalmente;
- botão 3D funciona;
- botão 2D no 3D funciona;
- reprodução 2D muda de mês a cada ~1,5 s;
- reprodução 3D muda de mês a cada ~1,5 s;
- consulta manual continua diária;
- PT/ES funciona;
- GloFAS mostra dados reais;
- DynQual carrega;
- saída hídrica carrega quando `outflow-ms.json` está publicado;
- pinch-to-zoom funciona no celular;
- 3D inclina/gira sem travar;
- `?` e `i` continuam acessíveis;
- nenhuma credencial foi adicionada ao commit.
