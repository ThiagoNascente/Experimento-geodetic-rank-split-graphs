# Execução exaustiva do programa_3

O `programa_3.py` verifica cada combinação de vértices individualmente. O padrão
é o mesmo grafo do `programa_2.py`: prisma complementar com 30 vértices e 120
arestas, construído a partir de um caminho de ordem 5, com conjuntos de tamanho
11. São C(30, 11) = 54.627.300 combinações.

## O laço de execução

A função `search_exhaustively` contém o laço principal:

```python
for bits in combinations(context._bits, size):
    independent = context._is_independent_bits(bits)
    stats.checked_combinations += 1
    # Entrega os conjuntos independentes ao callback e informa o progresso.
```

Cada bit representa um vértice. Assim, enumerar as tuplas de bits equivale a
enumerar as tuplas dos vértices originais, na mesma ordem. A chamada da
verificação acontece para cada tupla produzida. Não há descarte de ramos ou
contabilização de combinações que não passaram pelo laço.

Dentro de cada verificação, o critério continua sendo: S é independente quando
nenhum v de S pertence ao fecho de S sem v. Ao encontrar um v que prove a
dependência, essa verificação termina. Em seguida, o laço visita normalmente a
próxima combinação.

## O que é reaproveitado

As distâncias e os intervalos geodéticos são pré-calculados uma vez, pelo
`GeodeticConvexity`. Conjuntos e fechos usam máscaras de bits.

A classe `CachedGeodeticConvexity` acrescenta um cache LRU. A chave é o conjunto
inicial e o valor é seu fecho completo, incluindo todas as expansões necessárias.
Por exemplo, nas combinações {a,b,c} e {a,b,d}, o fecho de {a,b} pode ser usado
para testar tanto c quanto d. Remover o último vértice primeiro favorece esse
reaproveitamento entre combinações consecutivas.

Para calcular um fecho ainda ausente, o programa também reutiliza o fecho de um
prefixo menor. A identidade usada é:

```
Fecho(Fecho(T) união {x}) = Fecho(T união {x})
```

Se x já pertence ao fecho de T, o resultado está pronto. Caso contrário, o
cálculo incremental processa os pares envolvendo os vértices acrescentados.
Somente fechos completos entram no cache; resultados parciais obtidos por uma
interrupção antecipada de dependência não são armazenados como fechos.

O cache guarda até 65.536 entradas por padrão e remove as menos recentemente
usadas quando fica cheio. Um fecho removido pode precisar ser calculado
novamente. O limite evita armazenar os fechos de todas as milhões de
combinações. As estatísticas de consultas incluem as consultas recursivas dos
prefixos e, portanto, têm contagem diferente da quantidade de combinações.

## Comandos

Na raiz do projeto, execução completa:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3
```

Exemplo menor: 220 combinações de tamanho 3 num prisma de 12 vértices:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3 --ordem 3 --k 3
```

Desativar o cache de fechos, preservando os intervalos pré-calculados:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3 --ordem 3 --k 3 --cache-fechos 0
```

Também há `--plotar`, `--detalhar-grafo` e `--intervalo-progresso`, este último
em segundos. O programa pode ser executado pelo caminho do arquivo:

```powershell
.\venv\Scripts\python.exe Experimentos_diam_2/programa_3.py
```

## Resultado medido

Execução completa nesta máquina em 17/11/2026, com Python 3.14.7 e o ambiente
`venv` do projeto:

| Medição | Resultado |
| --- | ---: |
| Total de combinações | 54.627.300 |
| Combinações efetivamente verificadas | 54.627.300 |
| Conjuntos independentes de tamanho 11 | 0 |
| Consultas de fechos atendidas pelo cache | 54.673.033 |
| Consultas sem resultado no cache | 30.047.912 |
| Entradas finais no cache | 65.536 |
| Tempo da busca exaustiva | 72,130 s |
| Pré-processamento e busca | 72,135 s |

Os tempos excluem a inicialização do interpretador e as importações e variam
entre execuções. O resultado coincide com o da busca com poda do programa_2,
com a verificação individual de todas as combinações neste programa.

A suíte completa passou em 16 testes. Os novos testes comparam fechos,
independência e enumeração com a referência original em todos os 53 grafos não
isomorfos com até 5 vértices, usando caches desativados, pequenos e maiores.
Também verificam que cada candidato recebe sua própria chamada de teste, que
a função de busca com poda não é utilizada, que o cache respeita seu limite e
que o experimento possui um conjunto independente de tamanho 10 como testemunha
positiva. Para reproduzir:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```
