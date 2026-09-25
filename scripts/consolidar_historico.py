"""Consolida os JSONs semanais em dados/historico.csv.

- Backfill: para cada relatorios/relatorio_AAAA-MM-DD.md sem dados/AAAA-MM-DD.json,
  extrai o bloco ```json da seção 12 e salva em dados/.
- Gera dados/historico.csv com uma linha por data (colunas = união entre as datas).
- Nunca derruba o workflow: JSON inválido vira ::warning:: e o script sai com 0.
"""
import csv
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RELATORIOS = RAIZ / "relatorios"
DADOS = RAIZ / "dados"
CSV_SAIDA = DADOS / "historico.csv"

RE_DATA_MD = re.compile(r"^relatorio_(\d{4}-\d{2}-\d{2})\.md$")
RE_DATA_JSON = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")
RE_BLOCO_JSON = re.compile(r"```json\s*\n(.*?)\n\s*```", re.S)
RE_SECAO_12 = re.compile(r"^#{1,6}\s*12\.", re.M)
RE_SECAO_SEGUINTE = re.compile(r"^#{1,6}\s*13\.", re.M)

ESCALA_VISAO = {"subpeso": -2, "leve_subpeso": -1, "neutro": 0, "leve_sobrepeso": 1, "sobrepeso": 2}
ESCALA_CONVICCAO = {"baixa": 1, "media": 2, "alta": 3}
GRUPOS_ACHATADOS = ("brasil", "global", "retorno_real_aprox")
COLUNAS_FIXAS = ["data", "versao_schema", "regime_mercado", "pct_fonte_primaria"]

SEM_ACENTO = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçñ", "aaaaaeeeeiiiiooooouuuucn")


def avisar(msg):
    print(f"::warning::{msg}")


def slug(texto):
    texto = str(texto).lower().translate(SEM_ACENTO)
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def extrair_json_do_relatorio(md):
    """Bloco ```json da seção 12; se não achar a seção, usa o último bloco json do arquivo."""
    inicio = RE_SECAO_12.search(md)
    if inicio:
        fim = RE_SECAO_SEGUINTE.search(md, inicio.end())
        trecho = md[inicio.end(): fim.start() if fim else len(md)]
        blocos = RE_BLOCO_JSON.findall(trecho)
        if blocos:
            return blocos[0]
    blocos = RE_BLOCO_JSON.findall(md)
    return blocos[-1] if blocos else None


def backfill():
    if not RELATORIOS.is_dir():
        return
    for md_path in sorted(RELATORIOS.glob("relatorio_*.md")):
        m = RE_DATA_MD.match(md_path.name)
        if not m:
            continue
        destino = DADOS / f"{m.group(1)}.json"
        if destino.exists():
            continue
        bloco = extrair_json_do_relatorio(md_path.read_text(encoding="utf-8"))
        if bloco is None:
            avisar(f"Nenhum bloco JSON em {md_path.relative_to(RAIZ)}")
            continue
        try:
            obj = json.loads(bloco)
        except json.JSONDecodeError:
            avisar(f"JSON inválido em {md_path.relative_to(RAIZ)}")
            continue
        destino.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"backfill: {destino.relative_to(RAIZ)}")


def valor_csv(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def achatar(prefixo, obj, linha):
    for chave, v in obj.items():
        nome = f"{prefixo}_{slug(chave)}"
        if isinstance(v, dict) and ("min" in v or "max" in v):
            vmin, vmax = v.get("min"), v.get("max")
            linha[f"{nome}_min"] = valor_csv(vmin)
            linha[f"{nome}_max"] = valor_csv(vmax)
            numericos = all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in (vmin, vmax))
            linha[f"{nome}_mid"] = valor_csv((vmin + vmax) / 2) if numericos else ""
        elif isinstance(v, dict):
            achatar(nome, v, linha)
        else:
            linha[nome] = valor_csv(v)


def linha_do_json(data, obj):
    linha = {
        "data": data,
        "versao_schema": valor_csv(obj.get("versao_schema", 1)),
        "regime_mercado": valor_csv(obj.get("regime_mercado")),
        "pct_fonte_primaria": valor_csv(obj.get("pct_fonte_primaria")),
    }
    for grupo in GRUPOS_ACHATADOS:
        if isinstance(obj.get(grupo), dict):
            achatar(grupo, obj[grupo], linha)
    for item in obj.get("visao_classes") or []:
        if not isinstance(item, dict) or not item.get("classe"):
            continue
        classe = slug(item["classe"])
        linha[f"visao_{classe}"] = valor_csv(ESCALA_VISAO.get(slug(item.get("visao", ""))))
        linha[f"conviccao_{classe}"] = valor_csv(ESCALA_CONVICCAO.get(slug(item.get("conviccao", ""))))
    for cenario in obj.get("cenarios") or []:
        if isinstance(cenario, dict) and slug(cenario.get("nome", "")) in ("base", "otimista", "pessimista"):
            linha[f"prob_{slug(cenario['nome'])}"] = valor_csv(cenario.get("probabilidade"))
    lacunas = obj.get("lacunas_de_dados")
    linha["n_lacunas"] = valor_csv(len(lacunas) if isinstance(lacunas, list) else None)
    return linha


def consolidar():
    linhas = []
    for json_path in sorted(DADOS.glob("*.json")):
        m = RE_DATA_JSON.match(json_path.name)
        if not m:
            continue
        try:
            obj = json.loads(json_path.read_text(encoding="utf-8"))
            if not isinstance(obj, dict):
                raise ValueError
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            avisar(f"JSON inválido em {json_path.relative_to(RAIZ)}")
            continue
        linhas.append(linha_do_json(m.group(1), obj))

    linhas.sort(key=lambda l: l["data"])
    colunas = list(COLUNAS_FIXAS)
    for linha in linhas:
        colunas += [c for c in linha if c not in colunas]

    with CSV_SAIDA.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas, restval="")
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"{CSV_SAIDA.relative_to(RAIZ)}: {len(linhas)} linha(s), {len(colunas)} coluna(s)")


def main():
    DADOS.mkdir(exist_ok=True)
    backfill()
    consolidar()


if __name__ == "__main__":
    try:
        main()
    except Exception as erro:  # nunca derrubar o workflow
        avisar(f"Falha ao consolidar histórico: {erro}")
    sys.exit(0)
