# Assignment 3 - іске қосу және тапсыру

**Serik Zhankuat, SE-2520**  
**Таңдалған тіл: Java 17.**

## Ішінде не бар?

- `src/Java/Algorithms.java`: DSU, Kruskal, Prim, Kosaraju SCC, DFS topological
  ordering, DAG shortest paths және route reconstruction.
- `submission.json`: дайын `{"language":"Java"}`. Бұл тапсырмада student ID
  өрісі талап етілмейді.
- `ANALYSIS.md`: ағылшынша correctness, complexity, edge cases, нақты benchmark.
- `tests/`: өз тесттері, күтілетін және нақты нәтижелер.
- `.github/workflows/`: Public checks және қосымша Student tests.
- `DEFENCE_KZ.md`: алгоритмдерді түсінуге арналған қысқа конспект.

Public тексерудің 36 жағдайы және state reset өтті. Қосымша 392 жағдай,
бір JVM ішіндегі 784 сұрау, 17 шекті көлемдегі граф, 9 route helper тесті өтті.
Benchmark үш өлшемде, әр әдіске жеті өлшемнен орындалды.
Бұл нәтижелер бағаны автоматты түрде қоймайды.

## Windows-та тексеру

ZIP-ті толық шығарып ал. VS Code-та осы папканы аш. Терминалда
`submission.json` тұрған папкада екеніңді тексер.

```powershell
java -version
javac -version
py -3 --version
py -3 tools/run.py --setup
py -3 tools/run.py --check
py -3 tests/run_tests.py
```

`java` және `javac` үшін JDK 17 немесе одан жаңа нұсқа қажет.
Python 3.12 немесе одан жаңа болуы керек. Python тек тесттерді жүргізеді,
негізгі шешім Java тілінде.

Main-ді жай Run бассаң, бағдарлама JSON жолын күтеді: ол меню шығармайды.
Мысалы, консольге мына бір жолды бер:

```json
{"task":"dag","n":5,"source":0,"edges":[[0,1,3],[0,2,8],[1,2,-7],[2,3,4]]}
```

Нәтижеде `acyclic=true`, `distance=[0,3,-4,0,null]`,
`parent_edge=[-1,0,2,3,-1]` болуы керек. Объект өрістерінің реті өзгеруі мүмкін.
Кіріс күтіп тұрған бағдарлама қате емес.

## GitHub-қа орналастыру

1. Оқытушының [шаблонын](https://github.com/RZhaniya/daa-assignment-3-graphs)
   аш. **Use this template -> Create a new repository** таңда.
2. Өз аккаунтыңда `daa-assignment-3-graphs` атты жеке (Private) repository
   жаса. Атауы бұрыннан бар болса, басқа бос атау таңда.
3. ZIP-тің ішіндегі жоба папкасын аш. Файлдарды repository түбіріне
   орналастыр: `submission.json`, `ANALYSIS.md`, `src/`, `tests/`
   бір деңгейде тұруы керек. Жоба тағы бір артық папканың ішіне кірмесін.
   ZIP файлының өзін жалғыз файл ретінде upload жасама.
4. GitHub Desktop немесе Git арқылы commit жасап, push жаса.
   Браузердегі **Add file -> Upload files** қолдансаң, файлдар мен папкаларды
   түгел, соның ішінде `.github` папкасын да жүкте.
5. **Actions** бөлімінен дәл сол соңғы commit үшін **Public checks**
   және **Student tests** нәтижелерін тексер. Қызыл белгі болса, әлі тапсырма.
6. Private repository болса, оқытушының дұрыс GitHub username-ын тексеріп,
   **Settings -> Collaborators -> Add people** арқылы қолжетімділік бер.
   Шаблон авторының атына қарап автоматты түрде болжама.

Осы архивті дайындау кезінде өз аккаунтыңда repository жасалып,
GitHub Actions орындалды деп есептеуге болмайды: жергілікті тесттер
мен GitHub-тағы тексерулер бөлек.

## Moodle-ға нақты не тапсырамын?

1. GitHub-та соңғы commit-тің толық бетін аш.
2. Оның URL-ін көшір. URL ішінде `/commit/` және толық commit SHA болады.
   Repository-дің басты бетін немесе `/tree/main` сілтемесін тапсырма.
3. Moodle тапсырмасындағы **Online text** өрісіне сол commit URL-ін қой.
   Қосымша ретінде жасыл Actions run сілтемесін қоса аласың.
4. Өз Moodle-ыңдағы deadline пен syllabus талаптарын тексер.
5. **Save changes**, содан кейін **Submit assignment** бас.
6. Статусы **Submitted for grading** болғанын тексер.

Архивтің өзі Moodle-ға submit жасалғанын білдірмейді. Deadline бұл PDF-те
жазылмаған; Moodle көрсеткен мерзім негізгі болып саналады.

## Балл және дайындық

Практикалық жұмыс - 50 балл; бөлек quiz - 50 балл. Шаблон бойынша quiz:
ағылшынша 20 сұрақ, 20 минут, бір әрекет. Он сұрақ - single-answer multiple
choice, он сұрақ - numerical. Нақты баға оқытушының бағалауына байланысты.

`ANALYSIS.md` ішінде AI көмегі туралы ашық disclosure бар.
Syllabus-тағы талапты өзің тексер және кодтың жұмысын түсініп ал.
