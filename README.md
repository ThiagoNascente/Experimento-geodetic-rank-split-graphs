# Ainda para realizar

Terminar programa_6, ainda precisa da hipótese para conjunto de envoltória mínimo, aparentemente é |V(G)|...

# MAC e Linux

Gere um ambiente virtual python

```bash
python3 -m venv venv
```

Ative o ambiente virtual

```bash
source .venv/bin/activate
```

Instale as libs, estando dentro da venv

```bash
pip install -r requirements.txt
```

*OBS.:* Talvez precise usar o seguinte para plotar os grafos 

```bash
sudo apt update
sudo apt install python3-tk
```

# Windows

Gere um ambiente virtual python

```bash
py -m venv venv
```

Ative o ambiente virtual

```bash
.\venv\Scripts\activate
```

Instale as libs, estando dentro da venv

```bash
pip install -r requirements.txt
```


# Deduções

Para executar os experimentos anteriores rode:

```bash
python -m 'Experimentos antigos.programa_1.py'
```

Para os novos experimentos, execute:

```bash
python -m experimentos_novos.exp_1.py
```


# Experimento de diâmetro 2: programa_2

Na raiz do projeto, execute no Windows:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_2
```

O padrão continua sendo o prisma complementar construído a partir de `path_graph(5)`,
com busca exata dos conjuntos convexamente independentes de tamanho 11. Para abrir
o desenho ao final, acrescente `--plotar`. Use `--detalhar-grafo` para listar os
vértices e as arestas; `--ordem` e `--k` permitem variar os parâmetros.

A busca usa intervalos geodéticos pré-calculados, máscaras de bits e poda de
superconjuntos dependentes. No caso padrão, resolveu as 54.627.300 combinações
com 21.127 extensões de subconjuntos verificadas, em aproximadamente 0,14 segundo
de busca nesta máquina. Resultado: nenhum conjunto independente de tamanho 11.

Para reproduzir as verificações e as medições:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
.\venv\Scripts\python.exe -m benchmarks.benchmark_programa_2 --amostras 100
```

A análise dos gargalos, as regras de poda e os limites das medições estão em
[Experimentos_diam_2/OTIMIZACAO.md](Experimentos_diam_2/OTIMIZACAO.md).

# Enumeração exaustiva: programa_3

Para verificar individualmente todas as combinações do experimento padrão:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3
```

O `programa_3.py` percorre todas as possibilidades com `itertools.combinations`,
reutilizando os intervalos geodéticos e um cache limitado de fechos completos.
O contador informa o número de combinações efetivamente verificadas. A execução
completa nesta máquina verificou 54.627.300 combinações em 72,13 segundos de
busca e encontrou zero conjuntos independentes de tamanho 11.

Um exemplo menor, que também imprime conjuntos independentes e seus fechos:

```powershell
.\venv\Scripts\python.exe -m Experimentos_diam_2.programa_3 --ordem 3 --k 3
```

O cache guarda até 65.536 entradas por padrão. Use `--cache-fechos 0` para
executar com apenas o pré-processamento dos intervalos, ou indique outro limite.
Use `--plotar` para abrir o desenho após a enumeração.

Consulte [Experimentos_diam_2/EXECUCAO_EXAUSTIVA.md](Experimentos_diam_2/EXECUCAO_EXAUSTIVA.md)
para entender o reaproveitamento dos fechos e reproduzir as verificações.
