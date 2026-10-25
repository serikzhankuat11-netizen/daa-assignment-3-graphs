# Қысқа дайындық: Graph Algorithms

Бұл файл нақты quiz жауаптары емес; код пен негізгі идеяларды түсінуге арналған.

## DSU

DSU «қай төбелер бір топта?» деген сұраққа жауап береді.
`find(v)` топтың түбірін табады. `union(a,b)` екі түрлі топты қосады.
Path compression іздеу кезінде жолдағы төбелерді бірден түбірге байлайды.
Union by size кіші топты үлкен топтың астына жалғайды.
Қайталанған union жаңа топ қоспайды. Rank пен size бір нәрсе емес.

Мысалы, 4 бөлек төбе бар. union(0,1) -> 3 топ, ең үлкені 2.
union(1,2) -> 2 топ, ең үлкені 3. union(0,2) -> өзгеріс жоқ.

English: "DSU maintains connected components. I use path compression and union
by size to make repeated operations efficient."

## Kruskal

Барлық қырды салмағы бойынша сұрыптаймыз. Ең жеңілінен бастаймыз.
Екі ұшы әртүрлі DSU тобында болса, қырды аламыз.
Бір топта болса, цикл жасайды, сондықтан алмаймыз.
Граф байланыспаса, minimum spanning forest шығады.

English: "Kruskal sorts edges by weight and uses DSU to avoid cycles.
It returns a minimum spanning forest."

## Prim

Бір төбеден бастап, ағашқа сырттан қосылатын ең жеңіл қырды аламыз.
Priority queue жеңіл қырды тез табады. Қыр апаратын төбе бұрын алынған болса,
ол ескірген candidate: өткізіп жібереміз.
Бір компонент аяқталған соң әлі бармаған төбеден қайта бастаймыз.

English: "Prim grows a tree using the cheapest frontier edge.
I restart it for every unvisited component."

## Kosaraju SCC

SCC ішіндегі әр төбеден басқа әр төбеге бағытталған жол бар.
Бірінші DFS аяқталу ретін сақтайды. Барлық қырдың бағытын аударамыз.
Сақталған ретті кері оқып, transpose графында DFS жасаймыз.
Әр жаңа іздеу бір SCC табады.
Condensation - әр SCC бір төбеге қысқартылған граф; онда цикл болмайды.

English: "Kosaraju uses two DFS passes and a transposed graph.
The second pass processes vertices in decreasing finish order."

## Topological order

u->v болса, u ретте v-ден бұрын тұруы керек.
Үш күй: 0 - бармаған, 1 - қазір DFS жолында, 2 - толық аяқталған.
Күйі 1 төбеге қыр табылса, цикл бар. Күйі 2 төбеге қыр болуы цикл емес.
Цикл жоқ болса, DFS аяқталу ретін кері аударамыз.
Бұл жобада DFS recursion емес, массив-стекпен орындалады.

English: "An edge to an active vertex detects a directed cycle.
Otherwise, reversed DFS finish order is topological."

## DAG shortest paths

Алдымен бүкіл графта цикл жоқ екенін тексереміз.
Source-қа distance=0, қалғандарына null береміз.
Топологиялық ретпен жүріп, `dist[u] + weight < dist[v]` болса жаңартамыз.
u жетпейтін төбе болса, оны өткіземіз.
Теріс салмаққа болады: DAG-та цикл жоқ.
Source-тан жетпейтін жерде цикл болса да, acyclic=false қайтады.

`parent_edge[v]` алдыңғы төбенің нөмірі емес, edges массивіндегі қыр ID-і.
Route helper осы ID арқылы target-тен source-қа кері жүреді де, тізімді аударады.

English: "I relax edges in topological order after checking the whole graph
for cycles. Parent edge IDs let me reconstruct a shortest route."

## Есте сақтайтын кесте

| Әдіс | Уақыт | Негізгі құрал |
|---|---|---|
| DSU | O(n + q alpha(n)) amortised | parent, size |
| Kruskal | O(n + m log(m+1)) | сұрыптау + DSU |
| Prim | O(n + m log(m+1)) | adjacency + priority queue |
| Kosaraju | O(n+m) expected | екі DFS + transpose + hash set |
| DFS topo | O(n+m) | үш күй + finish order |
| DAG paths | O(n+m) | topo + relaxation |
| Route helper | O(L) | parent edge-тер |

Forest-та n-c қыр бар: n - төбе саны, c - компонент саны.
Self-loop MST-ке кірмейді, ал бағытталған графта цикл болып саналады.
Negative distance=-1 болуы мүмкін, сондықтан unreachable үшін null қолданамыз.
Үлкен қосындыларға int емес, long қажет.
