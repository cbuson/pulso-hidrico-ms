# Pulso Hídrico MS — V0.8.6

Atualização de interface sobre a V8.5. Não substitui nem remove os dados já processados.

## O que muda

- interface bilíngue Português / Español com seletor PT / ES no cabeçalho;
- identidade visual em tons de água e tipografia ampliada;
- leitura lateral no próprio mapa para temperatura e P90 GloFAS;
- painel Dados reorganizado com fontes visíveis e links diretos;
- botão `?` ampliado com explicação metodológica, limites de interpretação, fontes primárias e bibliografia científica;
- botão `i` ampliado com autoria completa de Carlos Busón Buesa e Sandra Garcia Gabas, vínculos UFMS / PPGTA / FAENG, ORCID, Lattes, e-mail, instalação PWA e forma de citação;
- campos DOI e Zenodo preparados, mas deixados como `— / em preparação` até existir depósito real;
- mantém consulta diária e reprodução automática mensal;
- mantém rios PIN MS / IMASUL como geometria visível, descarga GloFAS como espessura e climatologia DynQual como cor.

## Instalação

Descompacte esta atualização sobre a pasta atual `pulso-hidrico-ms` e aceite substituir os arquivos de `docs/`.

Não apague `docs/data/`, `data/processed/` nem os arquivos GloFAS / DynQual já preparados.

Depois execute:

```text
SERVIDOR_9564.cmd
```

Abra `http://localhost:9564` e faça `Ctrl + Shift + R` uma vez.

A versão visível deve ser `V0.8.6 · 2001–2025`.
