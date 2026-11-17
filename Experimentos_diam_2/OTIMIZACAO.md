# Relatório das otimizações geodéticas

Este relatório reúne as alterações em [convexity_geodetic.py](../convexity_geodetic.py),
as otimizações da busca com poda do [programa_2.py](programa_2.py) e a enumeração
exaustiva com cache do [programa_3.py](programa_3.py). Também descreve as mudanças nas funções auxiliares e distingue
as melhorias de desempenho das mudanças de organização e medição.

A comparação usa a implementação original registrada no Git e os arquivos
atuais do projeto. As medições abaixo foram realizadas nesta máquina em
17/11/2026, com Python 3.14.7 e o ambiente `venv` do projeto.

## 1. Experimento e comportamento esperado

O experimento padrão parte de `nx.path_graph(5)`. A função `construir_grafo`
produz um grafo com 15 vértices, e `prisma_complementar` produz o prisma com
30 vértices e 120 arestas. Buscam-se conjuntos convexamente independentes de
tamanho 11:

```
C(30, 11) = 54.627.300 combinações
```

Denotaremos o fecho geodético de S por H(S). Um conjunto S é convexamente
independente quando, para todo v de S, v não pertence a H(S sem v).
A função pública `geodetic_rank` continua retornando esse teste como um booleano.

Os dois programas atuais resolvem a mesma pergunta, usando estratégias de
busca diferentes:

| Aspecto | Original | programa_2 atual | programa_3 |
| --- | --- | --- | --- |
| Visita cada combinação de tamanho k individualmente | Sim | Descarta famílias por poda | Sim |
| Reutiliza intervalos geodéticos pré-calculados | Não | Sim | Sim |
| Representa conjuntos por máscaras de bits | Não | Sim | Sim |
| Reutiliza fechos ao ampliar um subconjunto | Não | Durante a busca | Por prefixos e cache |
| Mantém cache LRU de fechos entre consultas | Não | Não | Sim, até 65.536 entradas por padrão |
| Resultado no caso padrão | Busca completa antiga não medida | 0 conjuntos independentes | 0 conjuntos independentes |

A contagem de extensões do programa_2 e a contagem de combinações verificadas
do programa_3 representam trabalhos diferentes. Uma extensão do programa_2
pode envolver um conjunto menor que k e permitir descartar muitas combinações.

## 2. Gargalos da implementação original

O programa original usava `itertools.combinations` para gerar todas as
combinações, convertia cada tupla em lista e chamava `geodetic_rank(G, S)`.
Para um conjunto de tamanho 11, essa função podia calcular até 11 fechos.

O `geodetic_hull` original repetia o seguinte procedimento até estabilizar:

1. Copiava o conjunto corrente para um novo `set`.
2. Percorria todos os pares de vértices do conjunto corrente.
3. Chamava `nx.has_path` para verificar a conectividade de cada par.
4. Chamava `nx.all_shortest_paths` e enumerava os caminhos mínimos desse par.
5. Acrescentava os vértices desses caminhos ao novo conjunto.

Pares já examinados voltavam a ser processados na iteração seguinte. As mesmas
buscas também eram repetidas em fechos de outros conjuntos, embora o grafo não
mudasse. Além disso, enumerar caminhos pode gerar muitos objetos quando vários
caminhos mínimos compartilham os mesmos vértices.

No perfil instrumentado de 50 combinações iniciais, foram observadas:

| Medição do perfil original | Resultado |
| --- | ---: |
| Chamadas a `all_shortest_paths` | 35.695 |
| Chamadas a `has_path` | 35.695 |
| Chamadas de funções, aproximadamente | 9,2 milhões |
| Tempo total instrumentado | 4,64 s |
| Tempo cumulativo associado a `all_shortest_paths` | 3,47 s |

Esses tempos incluem o custo do profiler. A seção de medições apresenta também
uma comparação sem instrumentação, sobre os mesmos 100 conjuntos nas duas
implementações.

## 3. Otimizações compartilhadas em convexity_geodetic.py

### 3.1. Contexto reutilizável: GeodeticConvexity.__init__

A classe `GeodeticConvexity` concentra os dados que dependem apenas do grafo:

| Estrutura nova | Conteúdo e finalidade |
| --- | --- |
| `nodes` | Tupla dos rótulos originais, na ordem de inserção do grafo. |
| `_index` | Dicionário que associa cada rótulo a uma posição inteira. |
| `_bits` | Um bit por posição, evitando reconstruir essa representação a cada consulta. |
| `_all_nodes` | Máscara contendo todos os vértices. |
| `_interiors` | Tabela com os vértices interiores dos intervalos de cada par. |
| `_partners` | Máscara dos parceiros de cada vértice cujos intervalos têm interior não vazio. |

As distâncias são calculadas uma vez com
`nx.all_pairs_shortest_path_length`, que usa buscas em largura para grafos sem
pesos. Elas permitem verificar a conectividade e construir os intervalos,
eliminando as chamadas repetidas a `has_path` durante os fechos. O dicionário de
distâncias é usado na preparação; as consultas posteriores usam as máscaras.

### 3.2. Intervalos sem enumerar todos os caminhos mínimos

Para vértices conectados u e v, um vértice w pertence a algum caminho mínimo
entre eles exatamente quando:

```
d(u, w) + d(w, v) = d(u, v)
```

O pré-processamento testa essa igualdade e armazena o resultado. Dessa forma,
a consulta recupera a união dos vértices dos caminhos mínimos, sem construir
cada caminho individualmente.

Somente os vértices interiores são armazenados, pois os extremos já pertencem
ao conjunto que está sendo fechado. Pares desconexos não acrescentam vértices.
Pares de vértices adjacentes também não têm interior a acrescentar.

Como o grafo é não direcionado, o intervalo de u e v é o mesmo de v e u. A
construção calcula cada par uma vez e preenche as duas posições da tabela.
A máscara `_partners` permite pular, no cálculo do fecho, os pares que não podem
acrescentar vértices.

### 3.3. Máscaras de bits: _mask e _vertices

Internamente, cada conjunto é um inteiro. Se a, b e c correspondem às posições
0, 1 e 2, o conjunto {a,c} é representado por `0b101`.

As operações principais passam a ser:

```python
uniao = A | B
intersecao = A & B
novos = B & ~A
quantidade = A.bit_count()
```

`_mask(vertices)` converte os rótulos para essa representação e verifica se
pertencem ao grafo. `_vertices(mask)` recupera os rótulos originais. Isso reduz
cópias de conjuntos, operações sobre strings e conversões no trecho mais
executado. Os resultados públicos continuam usando os nomes dos vértices.

Inteiros Python têm precisão arbitrária; essa representação também funciona
quando o conjunto exige mais bits que uma palavra de máquina. O custo das
operações acompanha o tamanho desses inteiros.

### 3.4. Fecho incremental: _extend_hull

A função `_extend_hull(closed, additions, target=0)` recebe um conjunto já
fechado e os vértices que serão acrescentados. Ela mantém duas máscaras:

- `processed`: vértices cujos pares anteriores já foram tratados.
- `pending`: vértices novos cujos pares ainda precisam ser examinados.

Ao retirar um vértice de `pending`, processa seus pares com os vértices de
`processed`, consultando os interiores pré-calculados. Os vértices descobertos
entram em `pending`. O procedimento continua até não haver pendências.

Assim, um par é processado uma vez nessa expansão, e pares inteiramente dentro
do fecho recebido não precisam ser revisitados. Essa reutilização é válida
porque o argumento `closed` já está fechado.

O método público `hull(vertices)` inicia esse procedimento com fecho vazio e
retorna o resultado como `set`. Ele mantém todas as expansões necessárias: a
otimização preserva o fecho completo, inclusive quando uma expansão habilita
novos pares que acrescentam outros vértices.

### 3.5. Interrupção durante o fecho: is_independent

O `geodetic_rank` original **já retornava False ao encontrar dependência**.
Entretanto, antes disso, calculava integralmente H(S sem v).

O novo método `is_independent` passa o vértice v como `target` para
`_extend_hull`. Assim que v aparece, a dependência está comprovada e o cálculo
desse fecho pode terminar. Não é necessário descobrir os outros vértices que
ainda entrariam nele.

Há duas utilizações distintas de `_extend_hull`:

| Utilização | Garantia do resultado |
| --- | --- |
| Sem `target` | Retorna um fecho completo. |
| Com `target`, quando o alvo é alcançado | Pode retornar um conjunto parcialmente expandido, suficiente para comprovar a dependência. |

Um resultado parcial não deve ser reutilizado como fecho completo. Na busca
com poda, um resultado que alcançou o alvo descarta a extensão. No cache do
programa_3, somente fechos completos são armazenados.

### 3.6. Funções públicas e compatibilidade

| Função ou método | Alteração em relação à versão original |
| --- | --- |
| `_context(G)` | Novo adaptador: reutiliza um contexto recebido ou cria um para o grafo informado. |
| `geodetic_hull(G, S)` | Preserva a chamada pública e delega ao método `hull` do contexto. |
| `geodetic_rank(G, S)` | Preserva a chamada pública e delega a `is_independent`, com teste por alvo. |
| `geodetic_rank_antiga(G, S)` | Reutiliza um único contexto nas consultas ao fecho-base e aos conjuntos com remoções. Mantém o critério de comparação de fechos. |

O cálculo único do fecho-base dentro de `geodetic_rank_antiga` já existia na
versão original; a melhoria nessa função é compartilhar o pré-processamento
entre as consultas.

Chamadas que recebem diretamente um grafo constroem um contexto a cada chamada.
Para aproveitar o pré-processamento em muitas consultas, deve-se criar uma
instância e reutilizá-la:

```python
import networkx as nx
from convexity_geodetic import GeodeticConvexity, geodetic_hull, geodetic_rank

G = nx.path_graph(4)
contexto = GeodeticConvexity(G)
print(geodetic_hull(contexto, [0, 3]))  # {0, 1, 2, 3}
print(geodetic_rank(contexto, [0, 3]))  # True
```

## 4. Otimizações específicas do programa_2.py

O `main` do programa_2 constrói o grafo e um único `GeodeticConvexity`. A busca
é realizada pelo novo método `independent_sets`, com os recursos compartilhados
descritos acima e as otimizações seguintes.

### 4.1. Poda de superconjuntos dependentes

A independência convexa é hereditária: todo subconjunto de um conjunto
independente também é independente. Equivalentemente, se T é dependente,
todo conjunto que contém T também é dependente.

Um exemplo simples está no caminho `a-b-c-d`. O conjunto T = {a,b,c} é
dependente, pois b pertence a H({a,c}). Acrescentar d mantém a dependência:
H({a,c,d}) também contém b. A busca pode descartar a extensão de T sem fazer
uma nova verificação para cada conjunto maior que o contenha.

Formalmente, se v pertence a H(T sem v) e S contém T, então T sem v está
contido em S sem v. Pela monotonicidade do fecho, v também pertence a
H(S sem v). Isso comprova a validade do descarte.

O algoritmo constrói os conjuntos em ordem, acrescentando um candidato por vez.
Ao detectar uma extensão dependente, elimina todas as combinações que
completariam aquele ramo até o tamanho k. O resultado continua sendo exato.

### 4.2. Exclusão de candidatos que já estão no fecho

Se o conjunto escolhido é S e um candidato x já pertence a H(S), então
S união {x} é dependente: ao remover x, os vértices restantes já o geram.

A operação `available = candidates & ~hull` retira esses candidatos usando
uma máscara de bits. Se restarem menos candidatos que o necessário para
atingir k, o ramo termina sem gerar combinações inviáveis.

### 4.3. Reutilização dos fechos com remoções

Durante a busca são mantidos H(S) e os fechos H(S sem v) de cada vértice
escolhido. Ao acrescentar x, utiliza-se a identidade:

```
H(H(S sem v) união {x}) = H((S sem v) união {x})
```

Isso permite ampliar um fecho existente, em vez de reconstruí-lo. Para testar
a remoção do novo vértice x, o resultado necessário é H(S), já disponível.
Os fechos são transmitidos aos descendentes da busca e descartados quando o
ramo termina. Esse reaproveitamento durante a busca é diferente do cache LRU
usado no programa_3.

### 4.4. Contagem e geração dos resultados

A classe nova `SearchStats` registra:

| Campo | Significado |
| --- | --- |
| `total_combinations` | C(n,k), total teórico de combinações de tamanho k. |
| `extensions_tested` | Quantidade de extensões de subconjuntos efetivamente examinadas. |
| `pruned_combinations` | Combinações de tamanho k eliminadas pelas podas. |
| `independent_sets` | Conjuntos independentes encontrados. |
| `resolved_combinations` | Propriedade que soma combinações podadas e conjuntos encontrados. |
| `elapsed_seconds` | Tempo decorrido na busca. |

Se um ramo precisa escolher q vértices dentre r candidatos restantes, ele
representa C(r,q) combinações. Essa contagem permite contabilizar o ramo
eliminado sem enumerar seus conjuntos.

Ao concluir uma busca completa:

```
pruned_combinations + independent_sets = total_combinations
```

A busca produz os resultados com `yield`, na ordem das combinações originais.
Eles podem ser impressos e consumidos sem armazenar a lista inteira.

## 5. Otimizações específicas do programa_3.py

O programa_3 mantém a enumeração de todas as possibilidades. Ele acrescenta
reutilização de fechos completos para reduzir o custo das verificações.

### 5.1. Enumeração individual: search_exhaustively

O trecho central da função é:

```python
for bits in combinations(context._bits, size):
    independent = context._is_independent_bits(bits)
    stats.checked_combinations += 1
```

Cada tupla representa uma combinação dos vértices originais. Cada combinação
recebe sua própria chamada de verificação, e o contador avança depois dela.
A função não utiliza a busca com poda de `independent_sets`.

Ao encontrar uma prova de dependência dentro de uma combinação, sua
verificação pode terminar; a combinação seguinte continua sendo visitada.
Isso preserva o comportamento de decisão antecipada já presente na função de
independência original.

`itertools.combinations` já gerava resultados sob demanda na versão original.
O programa_3 mantém essa característica e evita a conversão de cada tupla em
uma lista de rótulos. As consultas são realizadas diretamente com os bits.
Rótulos são recuperados quando um conjunto independente precisa ser entregue
ao callback de resultados.

### 5.2. Cache de fechos completos: CachedGeodeticConvexity

A classe nova `CachedGeodeticConvexity` herda o pré-processamento e o cálculo
incremental de `GeodeticConvexity`. Seu construtor cria `_cached_hull` com
`functools.lru_cache`:

- A chave é a máscara do conjunto inicial.
- O valor é a máscara de seu fecho completo.
- O limite padrão é de 65.536 entradas.
- Ao atingir o limite, remove a entrada usada há mais tempo.

Assim, consultar novamente um conjunto ainda presente no cache recupera seu
fecho sem recalculá-lo. Um resultado removido pode precisar ser calculado
novamente; o limite controla o crescimento da memória.

### 5.3. Reaproveitamento de prefixos: _compute_hull

Mesmo quando o fecho pedido não está no cache, `_compute_hull` pode aproveitar
um fecho menor já calculado. O método retira o último vértice x do conjunto,
consulta H(T) para os vértices restantes e calcula:

```
H(T união {x}) = H(H(T) união {x})
```

Se x já pertence a H(T), o fecho está pronto. Caso contrário,
`_extend_hull` processa somente a expansão necessária. As consultas recursivas
chegam ao conjunto vazio quando ainda não existe um resultado reutilizável.

Os fechos de prefixos também ficam sujeitos ao limite do cache. O resultado
armazenado sempre corresponde ao fecho completo da chave consultada.

### 5.4. Ordem dos testes: _is_independent_bits

O método testa primeiro a remoção do último vértice da combinação, considerando
a ordem de inserção dos vértices no grafo. Essa escolha favorece o cache:
combinações consecutivas frequentemente compartilham o início.

Por exemplo, ao testar {a,b,c} e depois {a,b,d}, a primeira consulta de cada
verificação pode usar H({a,b}). Se esse fecho ainda estiver no cache, ele é
reutilizado. A ordem dos vértices testados não muda o critério de independência.

Com o cache ativo, o método consulta fechos completos. Com
`--cache-fechos 0`, ele usa os intervalos pré-calculados e pode interromper a
expansão assim que o alvo de dependência aparece, como em `is_independent`.

### 5.5. Demais métodos e estatísticas

| Função, método ou classe | Papel na implementação |
| --- | --- |
| `CachedGeodeticConvexity.is_independent` | Adapta rótulos de vértices ao teste por bits e ao cache. |
| `CachedGeodeticConvexity.hull` | Recupera ou calcula um fecho completo e retorna os rótulos como `set`. |
| `cache_info` | Expõe acertos, consultas ausentes e tamanho do cache para medição. |
| `search_exhaustively` | Percorre todas as combinações e entrega os resultados ao callback, sem acumulá-los internamente. |
| `ExhaustiveSearchStats` | Registra total, combinações verificadas, conjuntos independentes e tempo. |

O contador `checked_combinations` representa as combinações efetivamente
verificadas. Os contadores de cache também incluem consultas recursivas dos
prefixos. Portanto, acertos e consultas ausentes do cache não devem ser
interpretados como quantidades de combinações.

## 6. Funções auxiliares, importações e execução

### 6.1. Construção dos grafos

Os corpos das três funções abaixo mantêm a construção original dos vértices e
das arestas. A alteração nesses arquivos foi tornar as dependências explícitas:

| Arquivo e função | Alteração nas importações | Efeito |
| --- | --- | --- |
| `grafo_diam_2.py`: `construir_grafo` | `from libs import *` substituído por `import networkx as nx`. | Permite carregar a construção sem carregar todos os módulos agregados por `libs`. |
| `grafo_complemento.py`: `gerar_complemento` | Mesma substituição por NetworkX explícito. | Reduz o acoplamento com o agregador e sua cadeia de importações. |
| `prisms.py`: `prisma_complementar` | Importa NetworkX e `gerar_complemento` diretamente. | Declara as dependências realmente usadas e evita o retorno ao agregador. |

`convexity_geodetic.py` também deixou de importar `libs`. Essa reorganização
reduz as dependências circulares no caminho usado pelos novos programas.
Não foi medida uma aceleração isolada da inicialização, e as mudanças de
importação não representam um novo algoritmo de construção dos grafos.

### 6.2. Entrada dos programas e carregamento do desenho

Os programas usam `main(argv=None)` e a guarda
`if __name__ == "__main__"`. Importar seus módulos permite reutilizar as funções
sem iniciar a busca. Ambos aceitam execução como módulo ou pelo caminho do
arquivo, com parâmetros para ordem do caminho, tamanho k e progresso.

A função `plotar_grafo` continua com sua implementação original. Nos programas
atuais, ela é importada e chamada somente com `--plotar`. Assim, a execução
normal da busca evita carregar a interface gráfica e abrir uma janela ao final.
Os arquivos `libs.py` e `plotando_grafos.py` não foram editados nessas alterações;
a interface antiga de importação continua disponível.

### 6.3. Menos impressão no laço principal

O código original imprimia progresso a cada 1.000 combinações, apesar do
comentário mencionar 100.000. As versões atuais usam um intervalo de tempo,
com padrão de 5 segundos:

- No programa_2, a oportunidade de informar o progresso é verificada a cada
  512 extensões.
- No programa_3, ela é verificada a cada 16.384 combinações.

O agrupamento evita consultar o relógio a cada iteração e reduz a frequência
de impressão. O intervalo é aproximado, pois depende desses pontos de checagem.
Vértices e arestas são listados com `--detalhar-grafo`. Os informes e as classes
de estatísticas servem à observação do trabalho realizado; seus contadores
não constituem uma nova regra de independência.

## 7. Resultados medidos e interpretação

### 7.1. Mesma amostra, verificação original e otimizada

O benchmark usa 100 conjuntos de tamanho 11, sorteados com semente fixa
`20261117`. As duas implementações recebem os mesmos conjuntos e seus
resultados são comparados. O contexto é pré-calculado uma vez e reutilizado
na versão otimizada, sem a busca com poda nessa comparação de consultas.

| Medição | Tempo |
| --- | ---: |
| Verificação original dos 100 conjuntos | 4,599739 s |
| Pré-processamento do contexto otimizado | 0,002352 s |
| Verificação otimizada dos mesmos 100 conjuntos | 0,000437 s |
| Pré-processamento e verificação otimizada da amostra | 0,002789 s |

O ganho nessa amostra foi de aproximadamente 1.649 vezes, incluindo o
pré-processamento. Essa medição avalia o conjunto das mudanças do contexto e
do teste de independência. Não foi medido separadamente o ganho de cada
máscara, estrutura ou função.

### 7.2. Busca completa com poda: programa_2

| Medição | Resultado |
| --- | ---: |
| Combinações de tamanho 11 contabilizadas | 54.627.300 |
| Extensões de subconjuntos efetivamente examinadas | 21.127 |
| Combinações eliminadas por poda | 54.627.300 |
| Conjuntos independentes de tamanho 11 | 0 |
| Tempo da busca | 0,137110 s |

Essa execução resolve todas as possibilidades usando a propriedade da poda;
o contador de extensões não representa 54 milhões de verificações individuais.

### 7.3. Busca completa individual: programa_3

| Medição | Resultado |
| --- | ---: |
| Total de combinações de tamanho 11 | 54.627.300 |
| Combinações efetivamente verificadas | 54.627.300 |
| Conjuntos independentes de tamanho 11 | 0 |
| Consultas de fechos atendidas pelo cache | 54.673.033 |
| Consultas sem resultado no cache | 30.047.912 |
| Entradas finais no cache | 65.536 |
| Tempo da busca | 72,130 s |
| Pré-processamento e busca | 72,135 s |

Ambos os programas encontraram zero conjuntos independentes de tamanho 11 no
mesmo grafo. A diferença de tempo entre eles acompanha a diferença entre
podar famílias de combinações e verificar cada combinação individualmente.

O tempo da busca completa antiga não foi medido. O ganho da amostra de 100
conjuntos não deve ser apresentado como ganho medido sobre essa execução
completa. Os tempos excluem a inicialização do interpretador e as importações;
o desenho opcional é realizado após a medição. Os valores variam entre
execuções e refletem os parâmetros deste experimento.

## 8. Verificação de correção

A suíte atual passou em **16 testes**: nove para a implementação compartilhada
e a busca com poda e sete para a versão com cache e enumeração exaustiva.
Os arquivos são [test_convexity_geodetic.py](../tests/test_convexity_geodetic.py)
e [test_programa_3.py](../tests/test_programa_3.py).

As verificações incluem:

- Comparação dos fechos e das decisões de independência com a referência
  original em todos os subconjuntos dos 53 grafos não isomorfos com até
  5 vértices, incluindo comparação das enumerações resultantes.
- Seis grafos aleatórios de 7 vértices para o contexto compartilhado e a busca
  com poda, além de grafos desconexos com rótulos de tipos diferentes.
- Fecho que exige múltiplas expansões, entradas vazias, tamanhos maiores que
  o grafo, vértices ausentes e reutilização do contexto como retrato do grafo.
- Contabilidade das combinações podadas no programa_2.
- Caches desativados e com limites pequenos ou maiores no programa_3, incluindo
  reaproveitamento e remoção de entradas.
- Registro das quatro combinações de tamanho 3 de um caminho de 4 vértices,
  confirmando uma chamada por combinação; o teste também falha se a busca
  exaustiva chamar `independent_sets`, que implementa a poda.
- Um conjunto independente de tamanho 10 no grafo do experimento, usado como
  testemunha positiva, e comparações de candidatos de tamanho 11 com o original.

A busca com poda e a execução completa do programa_3 foram executadas no caso
padrão. No exemplo menor `--ordem 3 --k 3`, o programa_3 verificou as
220 combinações e encontrou 150 conjuntos independentes, com o mesmo resultado
com cache ativo e desativado.

O arquivo [benchmark_programa_2.py](../benchmarks/benchmark_programa_2.py)
conserva as funções de referência `original_hull` e `original_rank` para os
testes e para a comparação de desempenho.

## 9. Reprodução

Na raiz do projeto, execute a busca com poda:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_2
```

Execute a enumeração individual completa:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3
```

Para acompanhar um exemplo menor ou desativar o cache de fechos:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3 --ordem 3 --k 3
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3 --ordem 3 --k 3 --cache-fechos 0
```

Para reproduzir os testes e o benchmark da amostra:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
.\venv\Scripts\python.exe -m benchmarks.benchmark_programa_2 --amostras 100
```

O uso do programa_3 também está detalhado em
[EXECUCAO_EXAUSTIVA.md](EXECUCAO_EXAUSTIVA.md).

## 10. Limites e cuidados para reutilização

O contexto representa um grafo não direcionado e sem pesos no momento de sua
criação. Ele deve ser recriado após alterações nas arestas ou nos vértices;
não há invalidação automática dos intervalos nem dos fechos armazenados.

A preparação faz buscas a partir de cada vértice e tem laços cúbicos no pior
caso para construir os intervalos. A tabela tem n por n máscaras, cada uma
podendo conter n bits. O benefício é amortizar essa preparação em muitas
consultas sobre o mesmo grafo, como ocorre nos experimentos.

O programa_2 ainda pode explorar muitos subconjuntos quando poucas podas são
possíveis. O programa_3 executa C(n,k) verificações individuais mesmo quando
muitos fechos são reutilizados. Um cache maior pode aumentar os acertos, mas
também ocupa mais memória; seu efeito depende da ordem das consultas.

As melhorias medidas resultam das estruturas, da reutilização dos cálculos e
das estratégias de busca descritas neste relatório. A implementação usa
NetworkX e a biblioteca padrão do Python, sem processamento paralelo ou
compilação adicional dessas funções.
