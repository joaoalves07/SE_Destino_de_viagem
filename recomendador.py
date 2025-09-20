import json
import re
import sys
from typing import Any, Dict, List, Set


def padronizar_dinheiro(texto: str) -> float:      #Estou usando essa função para padronizar os valores em reais da base pois alguns estão com ",".
    nums = re.findall(r"[\d\.]+(?:,\d+)?", texto or "")
    if not nums:
        return 0.0
    return float(nums[0].replace(".", "").replace(",", "."))

def convert_passageiros(s: str) -> int:    #Aqui eu pego o numero de passageiros e tranformo em apenas um número.
    s = (s or "").lower()
    if "1 pessoa" in s:
        return 1
    nums = re.findall(r"\d+", s)
    return sum(map(int, nums)) if nums else 1

def separar_palavras(txt: str) -> List[str]:    #Separei os textos pois estava tendo problema para ler eles na execução do programa.
    if not txt:
        return []
    partes = re.split(r",|/|;| e ", txt.lower())
    return [p.strip() for p in partes if p.strip()]

def normalizar_atividades(txt: str) -> List[str]:   #Usei isso para tirar os preços dos () pois estava saindo na leitura dos dados.
    txt = re.sub(r"\(r\$\s*[^)]*\)", "", txt or "", flags=re.I)
    return separar_palavras(txt)


def carregar_base(caminho: str) -> Dict[str, Any]:   #Carrega a base de dados.
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)

def listagem(db: Dict[str, Any]) -> List[Dict[str, Any]]:   #Tranformei em lista os orçamentos e os destinos.
    itens = []
    for faixa, lista in db.items():
        for it in lista:
            it = dict(it)
            it["_Faixa"] = faixa
            itens.append(it)
    return itens

def criar_menus(itens: List[Dict[str, Any]]) -> Dict[str, List[str]]:  #Aqui eu crio os menus para cada etapa, fiz assim para evitar ter que escrever menu por menu.
    faixas: List[str] = []
    for it in itens:
        if it["_Faixa"] not in faixas:
            faixas.append(it["_Faixa"])

    grupos_set: Set[int] = set(convert_passageiros(it.get("Integrantes", "")) for it in itens)
    grupos = [str(g) for g in sorted(grupos_set)]

    climas_set: Set[str] = set()
    for it in itens:
        climas_set.update(separar_palavras(it.get("Clima", "")))
    climas = sorted(climas_set)

    ativ_set: Set[str] = set()
    for it in itens:
        ativ_set.update(normalizar_atividades(it.get("Atividade", "")))
    atividades = sorted(ativ_set)

    return {"faixas": faixas, "grupos": grupos, "climas": climas, "atividades": atividades}


def resposta_unica(titulo: str, opcoes: List[str], pode_pular: bool = True) -> str:   # Adiciona o título, as opções referentes a pergunta e também recebe a escolha do usuário.
    print(f"\n{titulo}")
    if pode_pular:
        print("  [0] Pular")
    for i, opc in enumerate(opcoes, start=1):
        print(f"  [{i}] {opc}")
    while True:
        esc = input("Escolha 1 opção (número): ").strip()
        if pode_pular and esc == "0":
            return ""
        if esc.isdigit():
            idx = int(esc)
            if 1 <= idx <= len(opcoes):
                return opcoes[idx - 1]
        print("Entrada inválida. Tente novamente.")

def prompt_opcao_multipla(titulo: str, opcoes: List[str], pode_pular: bool = True, limite: int = 10) -> List[str]:
    print(f"\n{titulo}")
    if pode_pular:
        print("  [0] Pular")
    for i, opc in enumerate(opcoes, start=1):
        print(f"  [{i}] {opc}")
    print("Você pode digitar múltiplos números separados por vírgula. Ex.: 1,3,5")
    while True:
        esc = input("Sua escolha: ").strip()
        if pode_pular and esc == "0":
            return []
        partes = [p.strip() for p in esc.split(",") if p.strip()]
        if all(p.isdigit() for p in partes):
            idxs = [int(p) for p in partes]
            if all(1 <= k <= len(opcoes) for k in idxs) and 1 <= len(idxs) <= limite:
                vistos = set()
                escolhidas = []
                for k in idxs:
                    if k not in vistos:
                        vistos.add(k)
                        escolhidas.append(opcoes[k - 1])
                return escolhidas
        print("Entrada inválida. Tente novamente.")


def respostas_filtro(dest: Dict[str, Any],  #Aqui eu pego as respostas e transformo elas em filtro para achar o destino pro usuário.
               faixa: str,
               grupo: str,
               climas: List[str],
               atividades: List[str]) -> bool:
    
    if faixa and dest["_Faixa"] != faixa:
        return False
    if grupo:
        if str(convert_passageiros(dest.get("Integrantes",""))) != grupo:
            return False
    if climas:
        dest_climas = set(separar_palavras(dest.get("Clima","")))
        if not dest_climas.intersection(set(c.lower() for c in climas)):
            return False
    if atividades:
        dest_ativ = [a.lower() for a in normalizar_atividades(dest.get("Atividade",""))]
        if not any(any(kw.lower() in a for a in dest_ativ) for kw in atividades):
            return False
    return True

def ordenar_filtros(dest: Dict[str, Any], atividades_escolhidas: List[str]) -> tuple:   #Isso serve para ordenar os filtros.
    # ordenar por (mais atividades casadas desc, valor total asc, nome cidade)
    dest_ativ = [a.lower() for a in normalizar_atividades(dest.get("Atividade",""))]
    hits = 0
    for kw in atividades_escolhidas:
        if any(kw.lower() in a for a in dest_ativ):
            hits += 1
    return (-hits, padronizar_dinheiro(dest.get("Valor total","999999")), dest.get("Cidade",""))

def mostrar_informacoes(dest: Dict[str, Any]):   #Vou imprimir as informações do destino que foi selecionado.
    print("\n=== Detalhes do destino selecionado ===")
    print(f"Cidade: {dest.get('Cidade','-')}  ({dest.get('Local','-')})")
    print(f"Faixa: {dest.get('_Faixa','-')}")
    print(f"Clima: {dest.get('Clima','-')}")
    print(f"Atividades: {dest.get('Atividade','-')}")
    print(f"Acomodação: {dest.get('Acomodacao','-')}")
    print(f"Alimentação: {dest.get('Alimentacao','-')}")
    print(f"Valor total: {dest.get('Valor total','-')}")
    print(f"Integrantes típicos: {dest.get('Integrantes','-')}")
    descricao = dest.get("Descrição") or dest.get("Descricao") or dest.get("description") or ""
    if descricao:
        print("\nDescrição:")
        print(descricao)
    else:
        print("\n(sem descrição cadastrada para este destino)")


def executar_programa(caminho_json: str):    #Execução do programa
    db = carregar_base(caminho_json)
    itens = listagem(db)
    op = criar_menus(itens)

    while True:

        faixa = resposta_unica("Me informe qual é a sua faixa de orçamento para essa viagem, ou pule, se desejar.", op["faixas"], pode_pular=True)
        grupo = resposta_unica("Me diga o tamanho do grupo de pessoas que vão na viagem, ou pule, se desejar.", op["grupos"], pode_pular=True)
        climas = prompt_opcao_multipla("Que tipos de clima você tem preferência?", op["climas"], pode_pular=False, limite=5)
        atividades = prompt_opcao_multipla("Que tipos de atividades você está buscando?", op["atividades"], pode_pular=True, limite=6)

        matches = [d for d in itens if respostas_filtro(d, faixa, grupo, climas, atividades)]

        if not matches:
            print("\nInfelizmente nao encontramos nenhum destino que se encaixe nos seus criterios :(.")
            resp = input("Deseja recomeçar? (s/n): ").strip().lower()
            if resp == "s":
                continue
            else:
                print("Encerrando. Até a próxima!")
                return

        matches.sort(key=lambda d: ordenar_filtros(d, atividades))
        print(f"\n=== {len(matches)} destino(s) respostas_filtronte(s) ===")
        for i, d in enumerate(matches, start=1):
            print(f"\n[{i}] {d.get('Cidade','-')} ({d.get('Local','-')})")
            print(f"     Faixa: {d.get('_Faixa','-')}  |  Clima: {d.get('Clima','-')}")
            print(f"     Valor total: {d.get('Valor total','-')}  |  Integrantes típicos: {d.get('Integrantes','-')}")
            print(f"     Atividades: {d.get('Atividade','-')}")

        while True:
            esc = input("\nDigite o número do destino para ver a descrição (ou 0 para recomeçar): ").strip()
            if esc == "0":
                break  # volta ao início (novos filtros)
            if esc.isdigit():
                idx = int(esc)
                if 1 <= idx <= len(matches):
                    mostrar_informacoes(matches[idx - 1])
                    prox = input("\nVer outro destino desta lista (número), '0' para recomeçar, ou 's' para sair: ").strip().lower()
                    if prox == "s":
                        print("Encerrando. Boas viagens!")
                        return
                    if prox == "0":
                        break
                    if prox.isdigit():
                        idx2 = int(prox)
                        if 1 <= idx2 <= len(matches):
                            mostrar_informacoes(matches[idx2 - 1])
                            continue
                    break
            print("Entrada inválida.")

def main():
    caminho_json = sys.argv[1] if len(sys.argv) > 1 else "destinos.json"
    executar_programa(caminho_json)

if __name__ == "__main__":
    main()
