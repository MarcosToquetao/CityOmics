# Pré-registro

| Arquivo | Conteúdo |
|---|---|
| `preregistration.md` | Rascunho do pré-registro no modelo do OSF para dados secundários, em inglês |
| `AMENDMENTS.md` | Emendas datadas, permitidas até a primeira abertura do cofre de 2026 |
| `analysis/` | Análise de poder da violência letal (código e saída; só dados de 2022–2025) |
| `OSF_DOI` | Criado depois do registro; contém só o DOI. É uma das duas chaves do cofre |

## Como registrar (prazo: 31/out/2026)

1. Preencha os campos `[fill in]` de `preregistration.md`: autores, afiliação e parecer ou dispensa do comitê de ética.
2. No OSF, crie um projeto e escolha **Registrations → "Preregistration for secondary data analysis"**. A opção "OSF Preregistration" também serve. Copie as seções.
3. **Embargo:** o OSF permite manter o registro privado por até 4 anos, com a data registrada. Use isso se quiser que o desenho só se torne público junto com os artigos.
4. Depois de aprovado, grave o DOI (formato `10.17605/OSF.IO/XXXXX`) em `prereg/OSF_DOI` e faça um commit. Esse commit é o carimbo de data no repositório.
5. A partir daí, qualquer mudança de plano vai para `AMENDMENTS.md` (e para o OSF) **antes** de abrir os dados de 2026.

## Reproduzir a análise de poder

```bash
python prereg/analysis/extract_letal.py ../MapaSegurancaSP/data/raw /tmp/letal_dp_trimestre.parquet
```

```bash
python prereg/analysis/power_letal.py /tmp/letal_dp_trimestre.parquet
```

O primeiro script lê só os arquivos de 2022–2025 e grava contagens agregadas por DP × trimestre, sem número de BO nem endereço.
