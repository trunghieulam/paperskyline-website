"""Page strings for the city and world pages, one table per language. City, keeper and country text is not here:
it comes from the game's packs. zh-Hans and id were drafted by the Web Engineer and checked by the City Writer.
"""

# The Paper Skyline server's permanent invite; to change it, edit here and re-run tools/cities.py.
DISCORD = 'https://discord.gg/MApRvYQu5g'
TIKTOK = 'https://www.tiktok.com/@paperskyline'
YOUTUBE = 'https://www.youtube.com/@paper-skyline'


def _en_the(name):
    return 'the ' + name[4:] if name.startswith('The ') else name


def _en_join(xs):
    return ', '.join(xs[:-1]) + (' and ' if len(xs) > 1 else '') + xs[-1]


def _zh_join(xs):
    return '、'.join(xs[:-1]) + ('和' if len(xs) > 1 else '') + xs[-1]


def _id_join(xs):
    return ', '.join(xs[:-1]) + (' dan ' if len(xs) > 1 else '') + xs[-1]


def _en_n(n, one, many):
    return f'{n} {one if n == 1 else many}'


# Country names that take "the" in an English sentence
_THE = {'US', 'GB', 'NL'}

T = {
    'en': dict(
        name='English', og_locale='en_US', sp=' ', skip='Skip to content', langs='Language', crumbs='Breadcrumb',
        nav=['Play', 'Cities', 'Minigames', 'News', 'Press', 'Support'],
        foot_nav=['Home', 'Cities', 'Minigames', 'News', 'For businesses', 'Press', 'Support', 'Privacy policy', 'Terms of use'],
        tagline='One sheet of paper, one city at a time.', discord='Join us on Discord',
        trademark='App Store is a trademark of Apple Inc. Google Play and the Google Play logo are trademarks of Google LLC.',
        home='Home', world='World',
        continents={'europe': 'Europe', 'asia': 'Asia', 'africa': 'Africa', 'north-america': 'North America',
                    'south-america': 'South America', 'oceania': 'Oceania'},
        the=_en_the, join=_en_join,
        country_in=lambda code, name: f'the {name}' if code in _THE else name,
        place=lambda name, country: name if name == country else f'{name}, {country}',
        city_title='{name} paper plane game | Paper Skyline', h1_small='paper plane game',
        city_desc=('Fly a paper plane over {place}, painted in ink and watercolour. '
                   'Meet its keepers, {elite} and {boss}, and the history behind them.'),
        hero_alt='The {name} skyline in ink and watercolour, as the game paints it',
        city_eb='City {n} of {total}', the_city='The city', the_landmark='The landmark',
        two_keepers='Two keepers', keepers_h2='Who keeps the wish in {name}.',
        keepers_lede=('An Elite wakes first; the Boss guards the wish itself. Hit their weak points for a BONK!, '
                      'land the last blow for a KO!, and each one grins and takes a bow.'),
        elite='The Elite', boss='The Boss',
        keeper_alt=lambda name, sub: f'{name}, {sub.split(" · ")[0].lower()}',
        relic='Guards a relic: the {relic}.', the_journal='The journal',
        route_from='The plane reaches {name} from {cities}.', route_start='Every journey starts in {name}.',
        route_next='Clear it and the map opens the way to {cities}.',
        route_look='Its own plane look is {look}, a {kind} look.',
        kinds={'trail': 'trail', 'paper': 'paper', 'ink': 'ink', 'colour': 'colour', 'fold': 'fold', 'style': 'style'},
        n_cities=lambda n: _en_n(n, 'city', 'cities'), n_countries=lambda n: _en_n(n, 'country', 'countries'),
        fly_on='Fly on.',
        hub_title='Cities | Paper Skyline', hub_h1='Where the plane flies.',
        hub_desc='The {n} cities of Paper Skyline, from {first} to {last}, each with its painting, its history and its two keepers.',
        country_title='{name} paper plane game | Paper Skyline',
        country_desc='Fly a paper plane over {cities} in Paper Skyline, and meet the keepers of {country}.',
        outline_alt="The outline of {country} from the game's Atlas",
        in_game=lambda n: _en_n(n, 'city', 'cities') + ' in the game', fly_over='Fly over {country}.',
        keepers_line='Its keepers are {keepers}.', city_more='More about {name}', planned_h3='Planned in {cont}',
        the_world='The world', more_of='More of {cont}', every_cont='Every continent',
        cont_title='{cont} in Paper Skyline | paper plane game',
        cont_desc='{n} of the {total} cities in Paper Skyline are in {cont}, across {countries}: {cities}.',
        world_title='The world of Paper Skyline | paper plane game',
        world_desc='Every city in Paper Skyline by continent and country: {total} cities, from {first} to {last}.',
        wish_title='Wish for the next city | Paper Skyline', wish_link='Wish for the next city', wish_h3='The next cities',
        wish_desc='Vote for the next city in Paper Skyline, the paper plane game: {n} planned cities, from {first} to {last}.',
        wish_eb=lambda n: _en_n(n, 'planned city', 'planned cities'), wish_h1='Where should the plane fly next?',
        wish_lede=('These cities are planned for Paper Skyline. Tap the one you want next: the counts help us '
                   'choose the cities for each release. Votes are anonymous, one per city on each browser.'),
        wish_nojs='Voting needs JavaScript. Without it, this is the list of planned cities.',
    ),
    'zh-Hans': dict(
        name='简体中文', og_locale='zh_CN', sp='', skip='跳到正文', langs='语言', crumbs='当前位置',
        nav=['下载', '城市', '小游戏', '新闻', '媒体资料', '帮助'],
        foot_nav=['首页', '城市', '小游戏', '新闻', '商务合作', '媒体资料', '帮助', '隐私政策', '使用条款'],
        tagline='一张纸，一座城市接着一座城市。', discord='加入我们的 Discord',
        trademark='App Store 是 Apple Inc. 的商标。Google Play 和 Google Play 徽标是 Google LLC 的商标。',
        home='首页', world='世界',
        continents={'europe': '欧洲', 'asia': '亚洲', 'africa': '非洲', 'north-america': '北美洲',
                    'south-america': '南美洲', 'oceania': '大洋洲'},
        the=lambda name: name, join=_zh_join,
        country_in=lambda code, name: name,
        place=lambda name, country: name if name == country else f'{country}{name}',
        city_title='{name}纸飞机游戏 | Paper Skyline', h1_small='纸飞机游戏',
        city_desc='让一架纸飞机飞过{place}，整座城市都用水墨和水彩画成。认识这里的守护者{elite}和{boss}，还有它们背后的历史。',
        hero_alt='游戏用水墨和水彩画出的{name}天际线',
        city_eb='第 {n} 座城市，共 {total} 座', the_city='这座城市', the_landmark='地标',
        two_keepers='两位守护者', keepers_h2='谁在守护{name}的心愿。',
        keepers_lede='精英守护者先醒来，首领守护者守着心愿本身。打中它们的弱点，会「砰！」一声；补上最后一击，就是「KO！」。然后它们都会笑着鞠躬。',
        elite='精英', boss='首领',
        keeper_alt=lambda name, sub: f'{name}，{sub.split(" · ")[0]}',
        relic='守护着一件古物：{relic}。', the_journal='日记',
        route_from='飞机从{cities}飞到{name}。', route_start='每一段旅程都从{name}开始。',
        route_next='闯过这里，地图就会通往{cities}。',
        route_look='这里独有的飞机外观是{kind}「{look}」。',
        kinds={'trail': '尾迹', 'paper': '纸张', 'ink': '墨水', 'colour': '颜色', 'fold': '折法', 'style': '造型'},
        n_cities=lambda n: f'{n} 座城市', n_countries=lambda n: f'{n} 个国家',
        fly_on='继续飞吧。',
        hub_title='城市 | Paper Skyline', hub_h1='纸飞机飞往的地方。',
        hub_desc='Paper Skyline 的 {n} 座城市，从{first}到{last}，每一座都有自己的画、自己的历史和两位守护者。',
        country_title='{name}纸飞机游戏 | Paper Skyline',
        country_desc='在 Paper Skyline 里，让纸飞机飞过{cities}，认识{country}的守护者。',
        outline_alt='游戏图集里的{country}轮廓',
        in_game=lambda n: f'游戏里的 {n} 座城市', fly_over='飞越{country}。',
        keepers_line='这里的守护者是{keepers}。', city_more='了解{name}', planned_h3='{cont}即将加入的城市',
        the_world='世界', more_of='{cont}的更多国家', every_cont='所有大洲',
        cont_title='Paper Skyline 里的{cont} | 纸飞机游戏',
        cont_desc='Paper Skyline 的 {total} 座城市里，有 {n} 座在{cont}，分布在 {countries}：{cities}。',
        world_title='Paper Skyline 的世界 | 纸飞机游戏',
        world_desc='按大洲和国家，列出 Paper Skyline 的每一座城市：共 {total} 座，从{first}到{last}。',
        homepage=dict(  # from the approved zh-CN Play listing, docs/store/google-play/1.9.0/listings.json
            title='Paper Skyline | 纸飞机游戏', desc='驾驶纸飞机飞越世界各地的城市，每次飞行后升级，飞得更远。',
            alt='水墨和水彩画出的巴黎日落天空，屋顶上飘着桃色的云，远处是埃菲尔铁塔',
            eyebrow='iPhone、iPad 和 Android', tag='让心愿起飞。',
            lede='一个暂时还不能出门旅行的男孩，把心愿写在笔记本的一页上，折成纸飞机，从窗口放飞。你来驾驶这架纸飞机，飞过用墨线和水彩画出的真实城市。',
            play_eb='玩法', play_h2='升级你的纸飞机',
            cards=[('每一次，都飞得更远一点', '掠过屋顶，看看自己能飞多远。距离、高度、速度和飞行时间，都会变成下一次飞行的资金。在工坊里升级发射器、机翼、机身、引擎和油箱。'),
                   ('挑战城市守护者', '找到弱点，看准时机，撞出关键的一击。下一段天空正在等你。'),
                   ('认识每座城市的居民', '每座城市有三个阶段，守护者一个比一个强。在巴黎认识埃米尔，在纽约认识伊玛妮，在东京认识花；完成他们的任务，开启阶段 2 和阶段 3。'),
                   ('收集新外观', '每天飞一飞，打开礼物，为你的纸飞机收集外观。'),
                   ('{n} 座城市等你去', '从巴黎、东京到里约和多伦多。把古物和明信片收进图集，任何城市都能用简单、普通或困难模式再玩一次。')],
            by_cont='按大洲浏览', all_cities='所有城市'),
    ),
    'id': dict(
        name='Bahasa Indonesia', og_locale='id_ID', sp=' ', skip='Langsung ke konten', langs='Bahasa', crumbs='Navigasi',
        nav=['Main', 'Kota', 'Minigame', 'Berita', 'Pers', 'Bantuan'],
        foot_nav=['Beranda', 'Kota', 'Minigame', 'Berita', 'Untuk bisnis', 'Pers', 'Bantuan', 'Kebijakan privasi', 'Ketentuan penggunaan'],
        tagline='Selembar kertas, satu demi satu kota.', discord='Gabung di Discord kami',
        trademark='App Store adalah merek dagang Apple Inc. Google Play dan logo Google Play adalah merek dagang Google LLC.',
        home='Beranda', world='Dunia',
        continents={'europe': 'Eropa', 'asia': 'Asia', 'africa': 'Afrika', 'north-america': 'Amerika Utara',
                    'south-america': 'Amerika Selatan', 'oceania': 'Oseania'},
        the=lambda name: name, join=_id_join,
        country_in=lambda code, name: name,
        place=lambda name, country: name if name == country else f'{name}, {country}',
        city_title='Game pesawat kertas {name} | Paper Skyline', h1_small='game pesawat kertas',
        city_desc=('Terbangkan pesawat kertas di atas {place}, dilukis dengan tinta dan cat air. '
                   'Temui para penjaganya, {elite} dan {boss}, serta sejarah di balik mereka.'),
        hero_alt='Kaki langit {name} dalam tinta dan cat air, seperti yang dilukis game ini',
        city_eb='Kota {n} dari {total}', the_city='Kotanya', the_landmark='Landmark-nya',
        two_keepers='Dua penjaga', keepers_h2='Siapa yang menjaga keinginan di {name}.',
        keepers_lede=('Penjaga Elite bangun lebih dulu; Penjaga Boss menjaga keinginan itu sendiri. Kenai titik lemah '
                      'mereka untuk BONK!, berikan pukulan terakhir untuk KO!, lalu masing-masing tersenyum dan membungkuk.'),
        elite='Elite', boss='Boss',
        keeper_alt=lambda name, sub: f'{name}, {sub.split(" · ")[0].lower()}',
        relic='Menjaga jimat: {relic}.', the_journal='Jurnal',
        route_from='Pesawat tiba di {name} dari {cities}.', route_start='Setiap perjalanan dimulai di {name}.',
        route_next='Selesaikan kota ini dan peta membuka jalan ke {cities}.',
        route_look='Tampilan pesawat khasnya adalah {kind} {look}.',
        kinds={'trail': 'jejak', 'paper': 'kertas', 'ink': 'tinta', 'colour': 'warna', 'fold': 'lipatan', 'style': 'gaya'},
        n_cities=lambda n: f'{n} kota', n_countries=lambda n: f'{n} negara',
        fly_on='Terus terbang.',
        hub_title='Kota | Paper Skyline', hub_h1='Ke mana saja pesawat ini terbang.',
        hub_desc='{n} kota di Paper Skyline, dari {first} sampai {last}, masing-masing dengan lukisan, sejarah, dan dua penjaganya.',
        country_title='Game pesawat kertas {name} | Paper Skyline',
        country_desc='Terbangkan pesawat kertas di atas {cities} di Paper Skyline, dan temui para penjaga {country}.',
        outline_alt='Siluet {country} dari Atlas game ini',
        in_game=lambda n: f'{n} kota di game ini', fly_over='Terbang di atas {country}.',
        keepers_line='Penjaganya adalah {keepers}.', city_more='Selengkapnya tentang {name}',
        planned_h3='Kota yang direncanakan di {cont}',
        the_world='Dunia', more_of='Lainnya di {cont}', every_cont='Semua benua',
        cont_title='{cont} di Paper Skyline | game pesawat kertas',
        cont_desc='{n} dari {total} kota di Paper Skyline ada di {cont}, tersebar di {countries}: {cities}.',
        world_title='Dunia Paper Skyline | game pesawat kertas',
        world_desc='Setiap kota di Paper Skyline menurut benua dan negara: {total} kota, dari {first} sampai {last}.',
        homepage=dict(  # drafted from the en-US Play listing, in the game's own words, for the City Writer to check
            title='Paper Skyline | game pesawat kertas',
            desc='Terbangkan pesawat kertas melintasi kota-kota di seluruh dunia, dan tingkatkan pesawatmu setelah setiap penerbangan.',
            alt='Langit Paris saat matahari terbenam dalam tinta dan cat air, dengan awan warna persik di atas atap dan Menara Eiffel',
            eyebrow='iPhone, iPad, dan Android', tag='Lipat sebuah keinginan. Terbangkan ke sana.',
            lede=('Seorang anak laki-laki yang belum bisa bepergian menulis keinginannya di selembar kertas buku catatan, '
                  'melipatnya menjadi pesawat kertas, lalu melemparnya keluar jendela. Kini kamu menerbangkannya di atas '
                  'kota-kota nyata yang dilukis dengan tinta dan cat air.'),
            play_eb='Cara bermain', play_h2='Rakit pesawat yang lebih baik',
            cards=[('Terbang sedikit lebih jauh setiap kali', 'Meluncurlah di atas atap dan lihat seberapa jauh kamu bisa terbang. Jarak, ketinggian, kecepatan, dan durasi jadi modal untuk penerbangan berikutnya. Tingkatkan peluncur, sayap, badan, mesin, dan tangki BBM di Bengkel.'),
                   ('Lewati para penjaga kota', 'Setiap kota punya Penjaga Elite dan Penjaga Boss. Kenai titik lemahnya untuk BONK! yang besar, atau rakit pesawat yang lebih kuat dan lewati mereka dengan pukulan biasa. Berikan pukulan terakhir untuk KO!'),
                   ('Kenali warga tiap kota', 'Tiga Tahap di tiap kota, masing-masing dengan penjaga yang lebih tangguh. Temui Émile di Paris, Imani di New York, dan Hana di Tokyo; misi mereka membuka Tahap 2 dan 3.'),
                   ('Kumpulkan tampilan baru', 'Terbanglah setiap hari, buka hadiah, dan kumpulkan tampilan untuk pesawat kertasmu.'),
                   ('{n} kota menunggumu', 'Dari Paris dan Tokyo sampai Rio dan Toronto. Kumpulkan jimat dan kartu pos untuk Atlasmu, dan mainkan lagi kota mana pun di tingkat Mudah, Sedang, atau Sulit.')],
            by_cont='Jelajahi menurut benua', all_cities='Semua kota'),
    ),
}
