(function () {
  "use strict";

  var SAMPLES = {
    en: [
      "The quick brown fox jumps over the lazy dog near the riverbank every morning.",
      "Good code is its own best documentation, but a short comment still helps a future reader.",
      "Debugging is twice as hard as writing the code in the first place, so write carefully.",
      "A clean commit message explains why a change was made, not just what was changed.",
      "Simplicity is prerequisite for reliability, and reliability is what makes software worth trusting.",
      "Formix processes everything in your browser, so your data never has to leave your device.",
      "Practice typing a little every day and your speed will improve faster than you expect.",
      "The best way to predict the future is to build it, one small working feature at a time.",
      "Rain tapped gently on the window while the city slowly settled into evening quiet.",
      "A short walk after lunch can clear your mind more than an extra cup of coffee.",
      "Learning a new skill always feels awkward at first, and that feeling is a good sign.",
      "The old library smelled of dust and paper, and nobody ever seemed to be in a hurry there.",
      "A good friend remembers the small details you mentioned only once, months ago.",
      "Stretching for five minutes before you start working can save you from a stiff back later.",
      "Time feels different when you are doing something you actually enjoy.",
      "Creativity rarely shows up on command, so it helps to keep a notebook nearby just in case.",
      "Saving a little money regularly matters more than saving a lot of money rarely.",
      "Gratitude turns an ordinary evening into something worth remembering the next morning.",
      "Patience is easiest to practice when nothing urgent is actually happening.",
      "Curiosity is simply the habit of asking one more question than feels comfortable.",
      "A team works best when everyone feels safe enough to admit a mistake out loud.",
      "The weather changed three times before noon, and nobody had planned for any of it.",
      "Music can turn a boring commute into something almost pleasant.",
      "A blank canvas is intimidating until you remind yourself that the first stroke rarely matters.",
      "Some books are read quickly, and some books quietly read you back.",
      "Sleep is the cheapest and most underrated tool for solving most problems.",
      "Deep focus usually arrives about twenty minutes after you stop checking your phone.",
      "Honesty is easier in the long run, even when it feels harder in the moment.",
      "Change rarely announces itself clearly; it mostly happens while you are looking elsewhere.",
      "Memory is less like a recording and more like a story we keep quietly editing.",
      "Laughter at the right moment can defuse almost any awkward situation.",
      "Home is less about the address and more about where you finally stop performing.",
      "Autumn arrives quietly, one slightly cooler morning at a time.",
      "A small act of kindness costs you almost nothing and is remembered for years.",
      "Growth usually looks like confusion right up until the moment it does not.",
      "Silence in a conversation is not always a problem that needs to be fixed.",
      "Courage is often just continuing to do something while still feeling afraid of it.",
      "Good habits are built in the boring middle, long after the motivation has faded.",
      "Dreams rarely arrive fully formed; most of them start out looking like bad ideas.",
      "The best questions usually start with noticing something that everyone else ignored.",
    ],
    ko: [
      "비 오는 날에는 따뜻한 커피 한 잔과 함께 책을 읽는 것이 가장 좋다.",
      "좋은 코드는 설명이 필요 없지만 짧은 주석 하나가 미래의 나를 도와준다.",
      "버그를 찾는 것은 코드를 처음 짜는 것보다 두 배는 더 어려운 일이다.",
      "꾸준히 연습하면 타자 속도는 생각보다 빠르게 늘어나니 조급해하지 않아도 된다.",
      "단순함은 안정성의 전제 조건이며 안정성이야말로 소프트웨어를 믿을 수 있게 만든다.",
      "작은 습관이 쌓이면 큰 변화를 만든다는 사실을 우리는 자주 잊고 산다.",
      "오늘 할 수 있는 일을 내일로 미루지 않는 것이 성공의 작은 비결이다.",
      "모든 처리는 브라우저 안에서 끝나므로 입력한 내용은 서버로 전송되지 않는다.",
      "창문 틈으로 들어오는 빗소리를 들으며 도시는 천천히 저녁 속으로 가라앉았다.",
      "점심을 먹고 잠깐 걷는 것이 커피 한 잔보다 머리를 더 맑게 해줄 때가 있다.",
      "새로운 것을 배울 때 처음엔 어색한 게 당연하고, 그 어색함은 오히려 좋은 신호다.",
      "오래된 도서관은 먼지와 종이 냄새가 났고 아무도 서두르지 않는 듯했다.",
      "좋은 친구는 몇 달 전에 지나가듯 한 말을 여전히 기억하고 있다.",
      "일을 시작하기 전에 오 분만 스트레칭을 해도 나중의 어깨 통증을 줄일 수 있다.",
      "정말 좋아하는 일을 할 때는 시간이 다르게 흐르는 것처럼 느껴진다.",
      "창의력은 부른다고 바로 오지 않으니 늘 작은 수첩을 곁에 두는 게 도움이 된다.",
      "적은 돈이라도 꾸준히 모으는 것이 가끔 큰돈을 모으는 것보다 더 중요하다.",
      "감사하는 마음은 평범한 저녁을 다음 날 아침까지 기억에 남는 순간으로 바꾼다.",
      "인내는 아무 급한 일이 없을 때 연습하기가 가장 쉬운 법이다.",
      "호기심이란 결국 조금 불편할 정도로 질문을 하나 더 던지는 습관일 뿐이다.",
      "팀은 누구나 실수를 소리 내어 인정할 수 있을 때 가장 잘 움직인다.",
      "정오가 되기도 전에 날씨가 세 번이나 바뀌었고 아무도 그걸 예상하지 못했다.",
      "음악은 지루한 통근길도 꽤 괜찮은 시간으로 바꿔 놓을 수 있다.",
      "빈 캔버스는 처음엔 두렵지만 첫 번째 선은 생각보다 중요하지 않다는 걸 떠올리면 된다.",
      "어떤 책은 빠르게 읽히고, 어떤 책은 조용히 나를 다시 읽어 나간다.",
      "잠은 가장 값싸면서도 가장 과소평가된, 대부분의 문제를 푸는 도구다.",
      "깊은 집중은 보통 휴대폰을 확인하지 않은 지 이십 분쯔음 지나야 찾아온다.",
      "솔직함은 당장은 더 힘들어도 길게 보면 결국 더 쉬운 길이다.",
      "변화는 대개 소리 없이 찾아오고, 다른 곳을 보고 있는 사이에 이미 일어나 있다.",
      "기억은 녹음기보다는 우리가 조금씩 고쳐 쓰는 이야기에 더 가깝다.",
      "적절한 순간의 웃음은 거의 모든 어색한 상황을 풀어준다.",
      "집이란 주소보다는 더 이상 연기하지 않아도 되는 곳을 뜻한다.",
      "가을은 조용히, 아주 조금씩 쌀쌀해지는 아침으로 다가온다.",
      "작은 친절은 거의 아무 비용도 들지 않지만 오래도록 기억에 남는다.",
      "성장은 그렇게 느껴지기 전까지는 대개 혼란처럼 보인다.",
      "대화 중의 침묵이 늘 고쳐야 할 문제인 것은 아니다.",
      "용기란 여전히 두려움을 느끼면서도 계속해 나가는 것일 때가 많다.",
      "좋은 습관은 의욕이 사라진 뒤, 지루한 중간 지점에서 만들어진다.",
      "꿈은 처음부터 완성된 모습으로 오지 않으며 대부분은 엉뚱한 생각처럼 시작된다.",
      "가장 좋은 질문은 보통 남들이 지나친 것을 알아채는 데서 시작된다.",
    ],
    ja: [
      "雨の日には温かいコーヒーを飲みながら本を読むのが一番の楽しみだ。",
      "良いコードは説明がいらないが、短いコメントが未来の自分を助けてくれる。",
      "バグを見つけるのは、コードを書くことの二倍も難しい作業だと言われている。",
      "毎日少しずつ練習すれば、タイピング速度は思ったより早く上達していく。",
      "シンプルさは信頼性の前提条件であり、信頼性こそソフトウェアを価値あるものにする。",
      "小さな習慣が積み重なって、やがて大きな変化を生み出すことを忘れがちだ。",
      "今日できることを明日に先延ばししないことが、成功への小さな秘訣である。",
      "すべての処理はブラウザ内で完結するため、入力内容はサーバーに送信されない。",
      "窓の隙間から聞こえる雨音を聞きながら、街はゆっくりと夜に沈んでいった。",
      "昼食後の短い散歩は、コーヒー一杯よりも頭をすっきりさせてくれることがある。",
      "新しいことを学ぶとき最初はぎこちなく感じるものだが、それは良い兆候だ。",
      "古い図書館はほこりと紙の匂いがして、誰も急いでいないように見えた。",
      "良い友人は何ヶ月も前にさらりと言った言葉を今でも覚えている。",
      "仕事を始める前に五分だけ伸びをすると、後の肩こりを防げることがある。",
      "本当に好きなことをしているときは、時間の流れ方が違って感じられる。",
      "創造力は呼んでもすぐには来ないので、小さなノートを常に持っておくと助かる。",
      "少しずつでも貯金を続けることは、たまに大きな額を貯めるより大事なことがある。",
      "感謝の気持ちは平凡な夜を、翌朝まで覚えていたくなる時間に変えてくれる。",
      "忍耐は何も急ぎの用事がないときに練習するのが一番やさしい。",
      "好奇心とは結局、少し気まずくなるくらい質問をもう一つ増やす習慣にすぎない。",
      "チームは誰もが声に出して間違いを認められるときに一番うまく機能する。",
      "正午になる前に天気が三回も変わり、誰もそれを予想していなかった。",
      "音楽は退屈な通勤時間すら、わりと悪くない時間に変えてくれることがある。",
      "真っ白なキャンバスは最初は怖いが、最初の一筆はそれほど重要ではないと思えばいい。",
      "ある本は速く読まれ、ある本は静かにこちらを読み返してくる。",
      "睡眠は最も安く、最も過小評価されている、たいていの問題を解く道具だ。",
      "深い集中力は、だいたい携帯を見なくなってから二十分ほど経って訪れる。",
      "正直であることは今は大変でも、長い目で見れば結局やさしい道になる。",
      "変化はたいてい静かに訪れ、よそを見ている間にすでに起きていることが多い。",
      "記憶は録音よりも、少しずつ書き直している物語に近いものだ。",
      "ちょうど良い瞬間の笑いは、ほとんどの気まずい空気をほどいてくれる。",
      "家とは住所よりも、もう演じなくていい場所のことを指す。",
      "秋は静かに、ほんの少しずつ涼しくなる朝としてやってくる。",
      "小さな親切はほとんど何の費用もかからないのに、長く記憶に残る。",
      "成長はそう感じられるようになるまで、たいてい混乱のように見える。",
      "会話の中の沈黙は、必ずしも直すべき問題というわけではない。",
      "勇気とはまだ怖さを感じながらも、続けていくことである場合が多い。",
      "良い習慣は、やる気が消えたあとの退屈な中間地点で作られる。",
      "夢は最初から完成した形では来ないもので、たいていはおかしな考えのように始まる。",
      "一番良い問いは、たいてい他の誰もが見過ごしたことに気づくところから始まる。",
    ],
    zh: [
      "下雨天最享受的事情就是一边喝着热咖啡一边安静地读书。",
      "好的代码不需要解释，但一句简短的注释能帮助未来的自己。",
      "调试代码的难度往往是编写代码本身的两倍，所以要格外细心。",
      "每天坚持练习一点打字，速度提升的会比你想象的更快。",
      "简单是可靠性的前提，而可靠性才是软件真正值得信赖的原因。",
      "小习惯日积月累，往往会带来意想不到的巨大改变。",
      "不要把今天能做的事情拖到明天，这是通向成功的小秘诀。",
      "所有处理都在浏览器内完成，你输入的内容不会被发送到服务器。",
      "听着窗缝里传来的雨声，整座城市慢慢沉入了夜色之中。",
      "午饭后的一段短暂散步，有时比一杯咖啡更能让头脑清醒。",
      "学习新事物时，一开始感到生疏是很正常的，这其实是个好信号。",
      "老图书馆里弥漫着灰尘和纸张的味道，似乎没有人着急赶时间。",
      "真正的朋友会记得你几个月前随口提过的一句小事。",
      "开始工作前花五分钟拉伸一下，往后或许就能少受肩颈疼痛的困扰。",
      "做自己真正喜欢的事情时，时间似乎流逝得完全不同。",
      "创造力并不会随叫随到，所以身边常备一本小笔记会很有帮助。",
      "持续地攒一点小钱，有时比偶尔攒一大笔钱更重要。",
      "感恩之心能把一个平凡的夜晚，变成第二天早上还会想起的时刻。",
      "耐心在没有任何紧急事情的时候，是最容易练习的。",
      "好奇心说到底，只是多问一个会让自己稍感不自在的问题的习惯。",
      "一个团队在每个人都能大声承认错误时，才能发挥得最好。",
      "还没到中午，天气就变了三次，而谁都没有为此做好准备。",
      "音乐可以把枯燥的通勤时间，变成一段还算愉快的时光。",
      "一张空白的画布一开始令人畏惧，但只要记住第一笔其实并不那么重要就好了。",
      "有些书会被人快速读完，也有些书在安静地把人重新读一遍。",
      "睡眠是解决大多数问题中，最廉价却也最被低估的方法。",
      "深度专注通常要在不看手机大约二十分钟之后才会出现。",
      "诚实在当下或许更难，但从长远来看反而是更轻松的那条路。",
      "变化往往悄无声息，常常是在你看向别处时就已经发生了。",
      "记忆与录音不同，它更像是一个被我们不断悄悄修改的故事。",
      "恰到好处的一笑，几乎能化解任何尴尬的场面。",
      "家与地址无关，更多是指那个不必再伪装自己的地方。",
      "秋天总是悄悄地，一点一点地带着凉意到来。",
      "一个小小的善举几乎不花什么成本，却能被人记住很多年。",
      "成长在被真正意识到之前，往往看起来更像是一片混乱。",
      "谈话中的沉默，并不总是需要被修补的问题。",
      "勇气很多时候，只是在依然感到害怕的情况下仍然继续向前。",
      "好习惯往往是在热情消退之后，那段无聊的中间阶段里养成的。",
      "梦想很少一开始就完整成形，大多数起初看起来都像是异想天开。",
      "最好的问题通常都始于注意到别人都忽略掉的那件小事。",
    ],
    es: [
      "El zorro marrón salta rápido sobre el perro perezoso cada mañana junto al río.",
      "El buen código es su propia mejor documentación, pero un comentario breve siempre ayuda.",
      "Depurar es el doble de difícil que escribir el código, así que hazlo con cuidado.",
      "Un buen mensaje de commit explica por qué se hizo un cambio, no solo qué cambió.",
      "La simplicidad es un requisito para la fiabilidad, y la fiabilidad hace que el software sea confiable.",
      "Formix procesa todo en tu navegador, así que tus datos nunca tienen que salir de tu dispositivo.",
      "Practica escribir un poco cada día y tu velocidad mejorará más rápido de lo que esperas.",
      "La mejor forma de predecir el futuro es construirlo, una pequeña función a la vez.",
      "La lluvia golpeaba suavemente la ventana mientras la ciudad se calmaba hacia la noche.",
      "Un paseo corto después de almorzar puede despejar tu mente más que una taza extra de café.",
      "Aprender una nueva habilidad siempre se siente incómodo al principio, y eso es buena señal.",
      "La vieja biblioteca olía a polvo y papel, y nadie parecía tener prisa allí.",
      "Un buen amigo recuerda los pequeños detalles que mencionaste solo una vez, hace meses.",
      "Estirar durante cinco minutos antes de empezar a trabajar puede evitarte dolor de espalda después.",
      "El tiempo se siente diferente cuando estás haciendo algo que realmente disfrutas.",
      "La creatividad rara vez aparece a pedido, así que ayuda tener un cuaderno cerca por si acaso.",
      "Ahorrar un poco de dinero con regularidad importa más que ahorrar mucho dinero de vez en cuando.",
      "La gratitud convierte una noche común en algo que vale la pena recordar al día siguiente.",
      "La paciencia es más fácil de practicar cuando no está pasando nada urgente en realidad.",
      "La curiosidad es simplemente el hábito de hacer una pregunta más de las que resultan cómodas.",
      "Un equipo funciona mejor cuando todos se sienten seguros para admitir un error en voz alta.",
      "El clima cambió tres veces antes del mediodía, y nadie había planeado para nada de eso.",
      "La música puede convertir un viaje aburrido en algo casi agradable.",
      "Un lienzo en blanco intimida hasta que te recuerdas que el primer trazo rara vez importa.",
      "Algunos libros se leen rápido, y algunos libros silenciosamente te leen a ti.",
      "El sueño es la herramienta más barata y subestimada para resolver la mayoría de los problemas.",
      "El enfoque profundo suele llegar unos veinte minutos después de dejar de revisar el teléfono.",
      "La honestidad es más fácil a largo plazo, aunque se sienta más difícil en el momento.",
      "El cambio rara vez se anuncia claramente; casi siempre ocurre mientras miras hacia otro lado.",
      "La memoria es menos como una grabación y más como una historia que seguimos editando en silencio.",
      "La risa en el momento justo puede desarmar casi cualquier situación incómoda.",
      "El hogar tiene menos que ver con la dirección y más con dónde finalmente dejas de actuar.",
      "El otoño llega en silencio, una mañana un poco más fresca a la vez.",
      "Un pequeño acto de bondad casi no cuesta nada y se recuerda durante años.",
      "El crecimiento suele parecer confusión justo hasta el momento en que deja de hacerlo.",
      "El silencio en una conversación no siempre es un problema que necesite resolverse.",
      "El valor suele ser simplemente seguir haciendo algo mientras todavía se le tiene miedo.",
      "Los buenos hábitos se construyen en el aburrido medio, mucho después de que se apague la motivación.",
      "Los sueños rara vez llegan completamente formados; la mayoría empieza pareciendo una mala idea.",
      "Las mejores preguntas suelen empezar al notar algo que todos los demás ignoraron.",
    ],
    vi: [
      "Con cáo nâu nhanh nhẹn nhảy qua con chó lười mỗi buổi sáng bên bờ sông.",
      "Mã nguồn tốt tự nó đã là tài liệu tốt nhất, nhưng một chú thích ngắn vẫn giúp người đọc sau này.",
      "Gỡ lỗi khó gấp đôi so với viết mã ngay từ đầu, vì vậy hãy viết cẩn thận.",
      "Một thông điệp commit rõ ràng giải thích lý do thay đổi, không chỉ là đã thay đổi gì.",
      "Sự đơn giản là điều kiện cần cho độ tin cậy, và độ tin cậy là điều khiến phần mềm đáng được tin tưởng.",
      "Formix xử lý mọi thứ ngay trong trình duyệt của bạn, nên dữ liệu của bạn không bao giờ phải rời khỏi thiết bị.",
      "Hãy luyện gõ một chút mỗi ngày và tốc độ của bạn sẽ cải thiện nhanh hơn bạn tưởng.",
      "Cách tốt nhất để dự đoán tương lai là tự xây dựng nó, từng tính năng nhỏ một.",
      "Mưa gõ nhẹ lên khung cửa sổ khi thành phố chầm chậm lắng vào buổi tối yên tĩnh.",
      "Một chuyến đi bộ ngắn sau bữa trưa có thể làm đầu óc tỉnh táo hơn một tách cà phê thêm.",
      "Học một kỹ năng mới luôn cảm thấy gượng gạo lúc đầu, và cảm giác đó là một dấu hiệu tốt.",
      "Thư viện cũ có mùi bụi và giấy, và dường như không ai ở đó từng vội vã.",
      "Một người bạn tốt nhớ những chi tiết nhỏ bạn chỉ nhắc đến một lần, nhiều tháng trước.",
      "Giãn cơ năm phút trước khi bắt đầu làm việc có thể giúp bạn tránh đau lưng sau này.",
      "Thời gian cảm thấy khác đi khi bạn đang làm điều mà bạn thực sự thích.",
      "Sự sáng tạo hiếm khi xuất hiện theo lệnh, vì vậy nên luôn mang theo một cuốn sổ nhỏ để đề phòng.",
      "Tiết kiệm một ít tiền đều đặn quan trọng hơn là tiết kiệm nhiều tiền một cách hiếm hoi.",
      "Lòng biết ơn biến một buổi tối bình thường thành điều đáng nhớ vào sáng hôm sau.",
      "Sự kiên nhẫn dễ thực hành nhất khi thực sự không có điều gì gấp gáp đang xảy ra.",
      "Sự tò mò đơn giản chỉ là thói quen hỏi thêm một câu hơn mức cảm thấy thoải mái.",
      "Một đội làm việc tốt nhất khi mọi người đều cảm thấy an toàn để thừa nhận lỗi của mình.",
      "Thời tiết thay đổi ba lần trước buổi trưa, và không ai đã chuẩn bị cho bất kỳ điều đó.",
      "Âm nhạc có thể biến một chuyến đi làm nhàm chán thành điều gần như thú vị.",
      "Một tấm vải trắng khiến ta sợ hãi cho đến khi ta tự nhắc rằng nét vẽ đầu tiên hiếm khi quan trọng.",
      "Một số cuốn sách được đọc nhanh, và một số cuốn sách lặng lẽ đọc lại chính ta.",
      "Giấc ngủ là công cụ rẻ nhất và bị đánh giá thấp nhất để giải quyết hầu hết các vấn đề.",
      "Sự tập trung sâu thường đến khoảng hai mươi phút sau khi bạn ngừng kiểm tra điện thoại.",
      "Sự trung thực dễ dàng hơn về lâu dài, dù nó cảm thấy khó khăn hơn ngay lúc đó.",
      "Sự thay đổi hiếm khi báo trước rõ ràng; nó thường xảy ra khi bạn đang nhìn sang nơi khác.",
      "Trí nhớ ít giống một bản ghi âm mà giống hơn một câu chuyện ta vẫn lặng lẽ chỉnh sửa.",
      "Một nụ cười đúng lúc có thể hóa giải hầu hết mọi tình huống ngượng ngùng.",
      "Nhà ít liên quan đến địa chỉ mà liên quan nhiều hơn đến nơi bạn cuối cùng không còn phải diễn.",
      "Mùa thu đến lặng lẽ, từng buổi sáng se lạnh hơn một chút.",
      "Một hành động tử tế nhỏ hầu như không tốn gì và được nhớ đến trong nhiều năm.",
      "Sự trưởng thành thường trông như sự bối rối cho đến đúng thời điểm nó không còn như vậy.",
      "Sự im lặng trong một cuộc trò chuyện không phải lúc nào cũng là vấn đề cần sửa.",
      "Sự can đảm thường chỉ là tiếp tục làm điều gì đó khi vẫn còn cảm thấy sợ nó.",
      "Những thói quen tốt được xây dựng trong khoảng giữa nhàm chán, rất lâu sau khi động lực đã phai nhạt.",
      "Những giấc mơ hiếm khi đến với hình dạng hoàn chỉnh; hầu hết bắt đầu như những ý tưởng tồi.",
      "Những câu hỏi tốt nhất thường bắt đầu từ việc nhận ra điều mà ai đó khác đã bỏ qua.",
    ],
    pt: [
      "A rápida raposa marrom salta sobre o cão preguiçoso perto do rio todas as manhãs.",
      "Um bom código é a sua própria melhor documentação, mas um comentário curto ainda ajuda um futuro leitor.",
      "Depurar é duas vezes mais difícil do que escrever o código em primeiro lugar, então escreva com cuidado.",
      "Uma boa mensagem de commit explica por que uma mudança foi feita, não apenas o que mudou.",
      "Simplicidade é pré-requisito para confiabilidade, e confiabilidade é o que torna o software digno de confiança.",
      "O Formix processa tudo no seu navegador, então seus dados nunca precisam deixar o seu dispositivo.",
      "Pratique digitar um pouco todos os dias e sua velocidade vai melhorar mais rápido do que você espera.",
      "A melhor forma de prever o futuro é construí-lo, uma pequena funcionalidade por vez.",
      "A chuva bateu suavemente na janela enquanto a cidade lentamente se acomodava na noite silenciosa.",
      "Uma curta caminhada depois do almoço pode clarear sua mente mais do que uma xícara extra de café.",
      "Aprender uma nova habilidade sempre parece estranho no início, e essa sensação é um bom sinal.",
      "A biblioteca antiga tinha cheiro de poeira e papel, e ninguém parecia estar com pressa ali.",
      "Um bom amigo lembra dos pequenos detalhes que você mencionou apenas uma vez, meses atrás.",
      "Alongar por cinco minutos antes de começar a trabalhar pode evitar uma dor nas costas mais tarde.",
      "O tempo parece diferente quando você está fazendo algo que realmente aprecia.",
      "A criatividade raramente aparece por comando, então ajuda manter um caderno por perto só por precaução.",
      "Economizar um pouco de dinheiro regularmente importa mais do que economizar muito dinheiro raramente.",
      "A gratidão transforma uma noite comum em algo que vale a pena lembrar na manhã seguinte.",
      "A paciência é mais fácil de praticar quando nada urgente está realmente acontecendo.",
      "Curiosidade é simplesmente o hábito de fazer mais uma pergunta do que parece confortável.",
      "Uma equipe funciona melhor quando todos se sentem seguros para admitir um erro em voz alta.",
      "O clima mudou três vezes antes do meio-dia, e ninguém havia planejado para nada daquilo.",
      "A música pode transformar um trajeto diário entediante em algo quase agradável.",
      "Uma tela em branco intimida até você se lembrar que o primeiro traço raramente importa.",
      "Alguns livros são lidos rapidamente, e alguns livros silenciosamente leem você de volta.",
      "O sono é a ferramenta mais barata e subestimada para resolver a maioria dos problemas.",
      "O foco profundo geralmente chega cerca de vinte minutos depois que você para de checar o celular.",
      "A honestidade é mais fácil no longo prazo, mesmo quando parece mais difícil no momento.",
      "A mudança raramente se anuncia claramente; geralmente acontece enquanto você está olhando para outro lugar.",
      "A memória é menos como uma gravação e mais como uma história que continuamos editando em silêncio.",
      "O riso no momento certo pode desarmar quase qualquer situação estranha.",
      "Lar tem menos a ver com o endereço e mais com onde você finalmente para de atuar.",
      "O outono chega silenciosamente, uma manhã um pouco mais fria por vez.",
      "Um pequeno ato de bondade custa quase nada e é lembrado por anos.",
      "O crescimento geralmente parece confusão até o momento em que deixa de parecer.",
      "O silêncio em uma conversa não é sempre um problema que precisa ser resolvido.",
      "Coragem muitas vezes é apenas continuar fazendo algo enquanto ainda se sente medo dele.",
      "Bons hábitos são construídos no meio tedioso, bem depois que a motivação desaparece.",
      "Sonhos raramente chegam totalmente formados; a maioria começa parecendo uma má ideia.",
      "As melhores perguntas geralmente começam ao notar algo que todos os outros ignoraram.",
    ],
    id: [
      "Rubah cokelat yang cepat melompati anjing pemalas di dekat sungai setiap pagi.",
      "Kode yang baik adalah dokumentasi terbaiknya sendiri, tetapi komentar singkat tetap membantu pembaca di masa depan.",
      "Men-debug dua kali lebih sulit daripada menulis kode itu sendiri, jadi tulislah dengan hati-hati.",
      "Pesan commit yang bersih menjelaskan mengapa sebuah perubahan dibuat, bukan hanya apa yang diubah.",
      "Kesederhanaan adalah prasyarat keandalan, dan keandalan adalah yang membuat perangkat lunak layak dipercaya.",
      "Formix memproses semuanya di browser Anda, sehingga data Anda tidak pernah perlu meninggalkan perangkat Anda.",
      "Berlatihlah mengetik sedikit setiap hari dan kecepatan Anda akan meningkat lebih cepat dari yang Anda kira.",
      "Cara terbaik untuk memprediksi masa depan adalah membangunnya, satu fitur kecil pada satu waktu.",
      "Hujan mengetuk lembut jendela sementara kota perlahan tenggelam ke dalam keheningan malam.",
      "Jalan kaki singkat setelah makan siang dapat menjernihkan pikiran Anda lebih dari secangkir kopi tambahan.",
      "Belajar keterampilan baru selalu terasa canggung di awal, dan perasaan itu adalah pertanda baik.",
      "Perpustakaan tua itu berbau debu dan kertas, dan tidak ada yang pernah terlihat terburu-buru di sana.",
      "Teman yang baik mengingat detail-detail kecil yang Anda sebutkan hanya sekali, berbulan-bulan lalu.",
      "Melakukan peregangan selama lima menit sebelum mulai bekerja dapat mencegah sakit punggung nantinya.",
      "Waktu terasa berbeda ketika Anda melakukan sesuatu yang benar-benar Anda nikmati.",
      "Kreativitas jarang muncul sesuai permintaan, jadi membantu untuk selalu membawa buku catatan kecil siapa tahu diperlukan.",
      "Menabung sedikit uang secara teratur lebih penting daripada menabung banyak uang sesekali.",
      "Rasa syukur mengubah malam biasa menjadi sesuatu yang layak dikenang keesokan paginya.",
      "Kesabaran paling mudah dipraktikkan ketika sebenarnya tidak ada hal mendesak yang terjadi.",
      "Keingintahuan hanyalah kebiasaan menanyakan satu pertanyaan lagi dari yang terasa nyaman.",
      "Sebuah tim bekerja paling baik ketika semua orang merasa cukup aman untuk mengakui kesalahan secara terbuka.",
      "Cuaca berubah tiga kali sebelum siang, dan tidak ada yang merencanakan untuk itu sama sekali.",
      "Musik dapat mengubah perjalanan yang membosankan menjadi sesuatu yang hampir menyenangkan.",
      "Kanvas kosong terasa menakutkan sampai Anda mengingatkan diri bahwa sapuan pertama jarang penting.",
      "Beberapa buku dibaca dengan cepat, dan beberapa buku diam-diam membaca Anda kembali.",
      "Tidur adalah alat paling murah dan paling diremehkan untuk menyelesaikan sebagian besar masalah.",
      "Fokus mendalam biasanya datang sekitar dua puluh menit setelah Anda berhenti memeriksa ponsel.",
      "Kejujuran lebih mudah dalam jangka panjang, meskipun terasa lebih sulit pada saat itu.",
      "Perubahan jarang mengumumkan dirinya dengan jelas; kebanyakan terjadi saat Anda melihat ke tempat lain.",
      "Memori lebih mirip sebuah cerita yang terus kita edit dengan diam-diam daripada sebuah rekaman.",
      "Tawa pada saat yang tepat dapat meredakan hampir semua situasi yang canggung.",
      "Rumah kurang berkaitan dengan alamat dan lebih berkaitan dengan tempat Anda akhirnya berhenti berpura-pura.",
      "Musim gugur datang dengan tenang, satu pagi yang sedikit lebih sejuk setiap kali.",
      "Sebuah tindakan kebaikan kecil hampir tidak membebani apa pun dan diingat selama bertahun-tahun.",
      "Pertumbuhan biasanya terlihat seperti kebingungan tepat sampai saat itu tidak lagi demikian.",
      "Keheningan dalam sebuah percakapan tidak selalu menjadi masalah yang perlu diperbaiki.",
      "Keberanian seringkali hanyalah terus melakukan sesuatu sementara masih merasa takut akan hal itu.",
      "Kebiasaan baik dibangun di tengah-tengah yang membosankan, jauh setelah motivasi memudar.",
      "Mimpi jarang datang dalam bentuk yang sudah lengkap; sebagian besar awalnya terlihat seperti ide buruk.",
      "Pertanyaan terbaik biasanya dimulai dengan memperhatikan sesuatu yang diabaikan semua orang lain.",
    ],
    de: [
      "Der schnelle braune Fuchs springt jeden Morgen am Flussufer über den faulen Hund.",
      "Guter Code ist seine eigene beste Dokumentation, aber ein kurzer Kommentar hilft trotzdem einem zukünftigen Leser.",
      "Debuggen ist doppelt so schwer wie das Schreiben des Codes selbst, also schreibe sorgfältig.",
      "Eine klare Commit-Nachricht erklärt, warum eine Änderung gemacht wurde, nicht nur, was geändert wurde.",
      "Einfachheit ist Voraussetzung für Zuverlässigkeit, und Zuverlässigkeit macht Software vertrauenswürdig.",
      "Formix verarbeitet alles in deinem Browser, sodass deine Daten dein Gerät niemals verlassen müssen.",
      "Übe jeden Tag ein wenig zu tippen, und deine Geschwindigkeit wird sich schneller verbessern, als du erwartest.",
      "Der beste Weg, die Zukunft vorherzusagen, ist, sie zu bauen, eine kleine Funktion nach der anderen.",
      "Regen klopfte sanft gegen das Fenster, während sich die Stadt langsam in den ruhigen Abend legte.",
      "Ein kurzer Spaziergang nach dem Mittagessen kann den Kopf mehr klären als eine zusätzliche Tasse Kaffee.",
      "Eine neue Fähigkeit zu lernen fühlt sich am Anfang immer unbeholfen an, und das ist ein gutes Zeichen.",
      "Die alte Bibliothek roch nach Staub und Papier, und niemand schien es dort jemals eilig zu haben.",
      "Ein guter Freund erinnert sich an die kleinen Details, die du nur einmal erwähnt hast, vor Monaten.",
      "Fünf Minuten Dehnen, bevor du mit der Arbeit beginnst, kann dir später Rückenschmerzen ersparen.",
      "Zeit fühlt sich anders an, wenn du etwas tust, das dir wirklich Freude macht.",
      "Kreativität erscheint selten auf Befehl, daher hilft es, immer ein Notizbuch für alle Fälle bereitzuhalten.",
      "Regelmäßig etwas Geld zu sparen ist wichtiger, als selten viel Geld zu sparen.",
      "Dankbarkeit verwandelt einen gewöhnlichen Abend in etwas, das sich am nächsten Morgen zu erinnern lohnt.",
      "Geduld lässt sich am leichtesten üben, wenn gerade nichts Dringendes passiert.",
      "Neugier ist einfach die Gewohnheit, eine Frage mehr zu stellen, als sich angenehm anfühlt.",
      "Ein Team funktioniert am besten, wenn sich alle sicher genug fühlen, einen Fehler laut zuzugeben.",
      "Das Wetter änderte sich dreimal vor Mittag, und niemand hatte sich darauf eingestellt.",
      "Musik kann einen langweiligen Arbeitsweg in etwas fast Angenehmes verwandeln.",
      "Eine leere Leinwand wirkt einschüchternd, bis man sich erinnert, dass der erste Strich selten wichtig ist.",
      "Manche Bücher werden schnell gelesen, und manche Bücher lesen einen still zurück.",
      "Schlaf ist das billigste und am meisten unterschätzte Mittel, um die meisten Probleme zu lösen.",
      "Tiefe Konzentration kommt meist etwa zwanzig Minuten, nachdem man aufgehört hat, das Handy zu checken.",
      "Ehrlichkeit ist auf lange Sicht einfacher, auch wenn sie sich im Moment schwerer anfühlt.",
      "Veränderung kündigt sich selten deutlich an; meist passiert sie, während man woanders hinschaut.",
      "Erinnerung ist weniger wie eine Aufnahme und mehr wie eine Geschichte, die wir still weiter bearbeiten.",
      "Lachen im richtigen Moment kann fast jede unangenehme Situation entschärfen.",
      "Zuhause hat weniger mit der Adresse zu tun und mehr mit dem Ort, an dem man endlich aufhört, etwas vorzuspielen.",
      "Der Herbst kommt leise, ein etwas kühlerer Morgen nach dem anderen.",
      "Eine kleine freundliche Geste kostet fast nichts und wird jahrelang erinnert.",
      "Wachstum sieht meist wie Verwirrung aus, genau bis zu dem Moment, in dem es das nicht mehr tut.",
      "Stille in einem Gespräch ist nicht immer ein Problem, das gelöst werden muss.",
      "Mut bedeutet oft einfach, etwas weiter zu tun, während man noch Angst davor hat.",
      "Gute Gewohnheiten entstehen in der langweiligen Mitte, lange nachdem die Motivation verschwunden ist.",
      "Träume kommen selten vollständig ausgeformt; die meisten sehen zunächst wie schlechte Ideen aus.",
      "Die besten Fragen beginnen meist damit, etwas zu bemerken, das alle anderen übersehen haben.",
    ],
  };

  function getLang() {
    var l = (document.documentElement.getAttribute("lang") || "en").slice(0, 2).toLowerCase();
    return SAMPLES[l] ? l : "en";
  }

  document.addEventListener("DOMContentLoaded", function () {
    var panel = document.getElementById("tt-panel");
    var passageEl = document.getElementById("tt-passage");
    var inputEl = document.getElementById("tt-input");
    var statusEl = document.getElementById("tt-status");
    var timeEl = document.getElementById("tt-time");
    var wpmEl = document.getElementById("tt-wpm");
    var accEl = document.getElementById("tt-accuracy");
    var bestEl = document.getElementById("tt-best");
    var restartBtn = document.getElementById("tt-btn-restart");
    var copyBtn = document.getElementById("tt-btn-copy");
    var copiedMsg = document.getElementById("tt-copied");
    var submitWrap = document.getElementById("tt-submit");
    var nicknameInput = document.getElementById("tt-nickname");
    var submitBtn = document.getElementById("tt-btn-submit");
    var submitStatus = document.getElementById("tt-submit-status");
    var lbWrap = document.getElementById("tt-leaderboard-wrap");
    var lbBody = document.getElementById("tt-leaderboard-body");
    var lbReset = document.getElementById("tt-leaderboard-reset");
    if (!panel || !passageEl || !inputEl) return;

    var resetAtMs = null;
    var resetTimerId = null;

    function renderResetCountdown() {
      if (!lbReset) return;
      if (!resetAtMs) {
        lbReset.hidden = true;
        return;
      }
      var diff = resetAtMs - Date.now();
      if (diff <= 0) {
        // 서버 시각 기준 초기화 시점을 지났으면(다음 로드 때 새 기간으로 갱신됨) 숨긴다.
        lbReset.hidden = true;
        return;
      }
      var totalHours = Math.ceil(diff / (60 * 60 * 1000));
      var days = Math.floor(totalHours / 24);
      var hours = totalHours % 24;
      var tpl = lbWrap.getAttribute("data-lb-reset-tpl") || "";
      lbReset.textContent = tpl.replace("{days}", days).replace("{hours}", hours);
      lbReset.hidden = false;
    }

    function startResetCountdown(resetAtIso) {
      if (!lbReset || !resetAtIso) return;
      resetAtMs = Date.parse(resetAtIso);
      if (!resetAtMs || isNaN(resetAtMs)) return;
      renderResetCountdown();
      if (resetTimerId) clearInterval(resetTimerId);
      // 시간 단위까지만 표시하므로 분 단위로 자주 갱신할 필요는 없다.
      resetTimerId = setInterval(renderResetCountdown, 60 * 1000);
    }

    var lang = getLang();
    var pool = SAMPLES[lang];
    var lastPassage = "";
    var passage = "";
    var startTime = null;
    var timerId = null;
    var totalKeystrokes = 0;
    var correctKeystrokes = 0;
    var finished = false;
    var lastWpm = 0;
    var lastAccuracy = 100;

    var statusIdle = panel.getAttribute("data-status-idle") || "";
    var statusActive = panel.getAttribute("data-status-active") || "";
    var statusDone = panel.getAttribute("data-status-done") || "";
    var bestNoneLabel = panel.getAttribute("data-best-none") || "";
    var bestKey = "formix-typing-best-" + lang;

    function pickPassage() {
      if (pool.length <= 1) return pool[0];
      var p;
      do {
        p = pool[Math.floor(Math.random() * pool.length)];
      } while (p === lastPassage);
      lastPassage = p;
      return p;
    }

    function renderPassage(text) {
      var html = "";
      for (var i = 0; i < text.length; i++) {
        var ch = text[i] === " " ? " " : text[i];
        html += '<span class="tt-char" data-i="' + i + '">' + ch + "</span>";
      }
      passageEl.innerHTML = html;
    }

    // 입력창(textarea)이 고정 줄 수(rows)만 보여주면, 영어처럼 글자 수가 많은
    // 문장이 3줄을 넘길 때 입력한 내용이 안 보이는 부분까지 스크롤되어 "짤리는"
    // 것처럼 보인다. 내용 높이(scrollHeight)에 맞춰 textarea 자체를 늘려서
    // 항상 전체 문장이 다 보이게 한다.
    function autoGrowInput() {
      inputEl.style.height = "auto";
      inputEl.style.height = inputEl.scrollHeight + "px";
    }

    function updatePassageHighlight(value) {
      var spans = passageEl.children;
      for (var i = 0; i < spans.length; i++) {
        var span = spans[i];
        span.classList.remove("is-correct", "is-incorrect", "is-current");
        if (i < value.length) {
          span.classList.add(value[i] === passage[i] ? "is-correct" : "is-incorrect");
        } else if (i === value.length) {
          span.classList.add("is-current");
        }
      }
    }

    function loadBest() {
      try {
        var raw = localStorage.getItem(bestKey);
        if (!raw) {
          bestEl.textContent = bestNoneLabel;
          return;
        }
        var data = JSON.parse(raw);
        bestEl.textContent = data.wpm + " WPM / " + data.accuracy + "%";
      } catch (e) {
        bestEl.textContent = bestNoneLabel;
      }
    }

    function maybeSaveBest(wpm, accuracy) {
      try {
        var raw = localStorage.getItem(bestKey);
        var data = raw ? JSON.parse(raw) : null;
        if (!data || wpm > data.wpm) {
          localStorage.setItem(bestKey, JSON.stringify({ wpm: wpm, accuracy: accuracy }));
          loadBest();
        }
      } catch (e) {
        /* localStorage 접근 불가 시 조용히 무시 */
      }
    }

    function tick() {
      if (!startTime) return;
      var elapsed = (performance.now() - startTime) / 1000;
      timeEl.textContent = elapsed.toFixed(1) + "s";
      var minutes = elapsed / 60;
      var wordsTyped = inputEl.value.length / 5;
      wpmEl.textContent = minutes > 0 ? Math.round(wordsTyped / minutes) : 0;
    }

    function stopTimer() {
      if (timerId) {
        clearInterval(timerId);
        timerId = null;
      }
    }

    function finish() {
      finished = true;
      stopTimer();
      var elapsed = Math.max((performance.now() - startTime) / 1000, 0.01);
      var minutes = elapsed / 60;
      var wordsTyped = passage.length / 5;
      lastWpm = Math.max(1, Math.round(wordsTyped / minutes));
      lastAccuracy = totalKeystrokes > 0 ? Math.max(0, Math.round((correctKeystrokes / totalKeystrokes) * 100)) : 100;
      timeEl.textContent = elapsed.toFixed(1) + "s";
      wpmEl.textContent = lastWpm;
      accEl.textContent = lastAccuracy + "%";
      statusEl.textContent = statusDone;
      statusEl.className = "status-pill is-valid";
      inputEl.disabled = true;
      copyBtn.disabled = false;
      maybeSaveBest(lastWpm, lastAccuracy);
      if (submitWrap) {
        submitWrap.hidden = false;
        submitStatus.textContent = "";
        submitStatus.className = "tt-submit-status";
        submitBtn.disabled = false;
      }
    }

    function reset() {
      finished = false;
      startTime = null;
      stopTimer();
      totalKeystrokes = 0;
      correctKeystrokes = 0;
      passage = pickPassage();
      renderPassage(passage);
      inputEl.value = "";
      inputEl.style.height = "auto";
      inputEl.disabled = false;
      copyBtn.disabled = true;
      copiedMsg.hidden = true;
      statusEl.textContent = statusIdle;
      statusEl.className = "status-pill is-idle";
      timeEl.textContent = "0.0s";
      wpmEl.textContent = "0";
      accEl.textContent = "100%";
      updatePassageHighlight("");
      if (submitWrap) submitWrap.hidden = true;
      inputEl.focus();
    }

    // 붙여넣기로 전체 문장을 한 번에 채우면 첫 입력과 완료가 거의 동시에 일어나
    // 경과 시간이 0.0초로 계산되는 문제가 있었다. 타자 속도 테스트의 취지 자체가
    // 직접 입력하는 속도를 재는 것이므로 붙여넣기(및 드래그 앤 드롭으로 텍스트를
    // 끌어다 놓는 것)는 아예 막는다.
    inputEl.addEventListener("paste", function (e) {
      e.preventDefault();
    });
    inputEl.addEventListener("drop", function (e) {
      e.preventDefault();
    });

    inputEl.addEventListener("beforeinput", function (e) {
      if (finished) {
        e.preventDefault();
        return;
      }
      if (e.inputType === "insertFromPaste" || e.inputType === "insertFromDrop") {
        e.preventDefault();
        return;
      }
      if (e.inputType && e.inputType.indexOf("insert") === 0) {
        var pos = inputEl.selectionStart;
        var insertedChar = (e.data && e.data.length > 0) ? e.data[0] : null;
        if (insertedChar !== null && pos < passage.length) {
          totalKeystrokes++;
          if (insertedChar === passage[pos]) correctKeystrokes++;
        } else if (insertedChar !== null) {
          totalKeystrokes++;
        }
      }
    });

    inputEl.addEventListener("input", function () {
      if (finished) return;
      if (!startTime) {
        startTime = performance.now();
        statusEl.textContent = statusActive;
        statusEl.className = "status-pill is-fixed";
        timerId = setInterval(tick, 100);
      }
      var value = inputEl.value;
      if (value.length > passage.length) {
        value = value.slice(0, passage.length);
        inputEl.value = value;
      }
      updatePassageHighlight(value);
      autoGrowInput();
      tick();
      if (value === passage) {
        finish();
      }
    });

    restartBtn.addEventListener("click", reset);

    copyBtn.addEventListener("click", function () {
      var prefix = panel.getAttribute("data-result-prefix") || "";
      var wpmLabel = panel.getAttribute("data-wpm-label") || "WPM";
      var accLabel = panel.getAttribute("data-accuracy-label") || "Accuracy";
      var url = panel.getAttribute("data-share-url") || "";
      var text = prefix + "\n" + wpmLabel + ": " + lastWpm + " WPM | " + accLabel + ": " + lastAccuracy + "%\n" + url;
      var done = function () {
        copiedMsg.hidden = false;
        setTimeout(function () {
          copiedMsg.hidden = true;
        }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, done);
      } else {
        try {
          var ta = document.createElement("textarea");
          ta.value = text;
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          document.body.removeChild(ta);
        } catch (e) {
          /* 복사 실패 시 조용히 무시 */
        }
        done();
      }
    });

    function escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, function (ch) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
      });
    }

    function renderLeaderboard(entries) {
      if (!lbBody) return;
      if (!entries || entries.length === 0) {
        lbBody.innerHTML = '<tr><td colspan="4" class="tt-leaderboard-status">' + escapeHtml(lbWrap.getAttribute("data-lb-empty") || "") + "</td></tr>";
        return;
      }
      var rows = entries.map(function (e, i) {
        return "<tr><td>" + (i + 1) + "</td><td>" + escapeHtml(e.nickname) + "</td><td>" + escapeHtml(e.wpm) + "</td><td>" + escapeHtml(e.accuracy) + "%</td></tr>";
      });
      lbBody.innerHTML = rows.join("");
    }

    function loadLeaderboard() {
      if (!lbWrap || !lbBody) return;
      lbBody.innerHTML = '<tr><td colspan="4" class="tt-leaderboard-status">' + escapeHtml(lbWrap.getAttribute("data-lb-loading") || "") + "</td></tr>";
      fetch("/api/leaderboard?lang=" + encodeURIComponent(lang) + "&limit=20")
        .then(function (res) {
          if (!res.ok) throw new Error("bad status");
          return res.json();
        })
        .then(function (data) {
          renderLeaderboard(data.entries);
          startResetCountdown(data.resetAt);
        })
        .catch(function () {
          lbBody.innerHTML = '<tr><td colspan="4" class="tt-leaderboard-status">' + escapeHtml(lbWrap.getAttribute("data-lb-error") || "") + "</td></tr>";
        });
    }

    if (nicknameInput) {
      try {
        var savedNickname = localStorage.getItem("formix-typing-nickname");
        if (savedNickname) nicknameInput.value = savedNickname;
      } catch (e) {
        /* localStorage 접근 불가 시 조용히 무시 */
      }
    }

    if (submitBtn) {
      submitBtn.addEventListener("click", function () {
        if (!finished) return;
        var nickname = (nicknameInput && nicknameInput.value ? nicknameInput.value : "").trim().slice(0, 20);
        try {
          if (nickname) localStorage.setItem("formix-typing-nickname", nickname);
        } catch (e) {
          /* 조용히 무시 */
        }
        submitBtn.disabled = true;
        submitStatus.className = "tt-submit-status";
        submitStatus.textContent = lbWrap.getAttribute("data-lb-submitting") || "";
        fetch("/api/leaderboard", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nickname: nickname, wpm: lastWpm, accuracy: lastAccuracy, lang: lang }),
        })
          .then(function (res) {
            if (res.status === 429) {
              submitStatus.className = "tt-submit-status is-error";
              submitStatus.textContent = lbWrap.getAttribute("data-lb-rate-limited") || "";
              submitBtn.disabled = false;
              return null;
            }
            if (!res.ok) throw new Error("bad status");
            return res.json();
          })
          .then(function (data) {
            if (!data) return;
            if (data.ok) {
              var successTpl = lbWrap.getAttribute("data-lb-success") || "";
              submitStatus.className = "tt-submit-status is-success";
              submitStatus.textContent = successTpl.replace("{rank}", data.rank);
              loadLeaderboard();
            } else {
              submitStatus.className = "tt-submit-status is-error";
              submitStatus.textContent = lbWrap.getAttribute("data-lb-error-submit") || "";
              submitBtn.disabled = false;
            }
          })
          .catch(function () {
            submitStatus.className = "tt-submit-status is-error";
            submitStatus.textContent = lbWrap.getAttribute("data-lb-error-submit") || "";
            submitBtn.disabled = false;
          });
      });
    }

    loadBest();
    reset();
    loadLeaderboard();
  });
})();
