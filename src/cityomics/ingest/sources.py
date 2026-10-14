"""Fontes de microdados da SSP-SP (spec-dados §1).

Os endereços seguem o padrão validado no MapaSegurancaSP (``pipeline/01_download.py``).
A SSP só serve 2022 em diante nesse formato; 2019–2021 devolvem 404.
"""

from __future__ import annotations

from dataclasses import dataclass

SSP_ASSETS = "https://www.ssp.sp.gov.br/assets/estatistica/transparencia"
YEARS = tuple(range(2022, 2027))


@dataclass(frozen=True)
class Source:
    name: str
    url_template: str

    def filename(self, year: int) -> str:
        return f"{self.name}_{year}.xlsx"

    def url(self, year: int) -> str:
        return self.url_template.format(year=year)


SSP_DADOS = Source("SPDadosCriminais", SSP_ASSETS + "/spDados/SPDadosCriminais_{year}.xlsx")
CELULARES = Source("CelularesSubtraidos",
                   SSP_ASSETS + "/baseDados/celularesSub/CelularesSubtraidos_{year}.xlsx")
SOURCES = (SSP_DADOS, CELULARES)

# Tabela oficial mensal por município (561 municípios; 565 = São Paulo, capital)
SSP_API_MENSAL = ("https://www.ssp.sp.gov.br/v1/OcorrenciasMensais/RecuperaDadosMensaisAgrupados"
                  "?ano={year}&grupoDelito=6&tipoGrupo=MUNIC%C3%8DPIO&idGrupo=565")
