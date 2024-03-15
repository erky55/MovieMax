import logging, asyncio

logging.basicConfig(level=logging.INFO)

import re

from aiohttp import ClientSession
from bs4 import BeautifulSoup
from swibots import *
from datetime import datetime as dt
from schedule import every
import swibots as s
from config import BOT_TOKEN, ADS_TOKEN, RESOLVED_URL, SHARE_URL
from aiohttp_client_cache import CachedSession, SQLiteBackend

tokenCache = {}

FeatureUrl = "https://5movierulz.vet/{}/page/{}"
Bollywood = "https://5movierulz.vet/bollywood-movie-free/"


async def get(url):
    async with CachedSession(cache=SQLiteBackend("moviez")) as ses:
        async with ses.get(url) as res:
            content = await res.read()
            return content


async def getLink(url):
    sp = await soup(url)
    try:
        return sp.find("a", "main-button").get("href")
    except Exception as er:
        print(er, url)
    return url

async def soup(url):
    return BeautifulSoup(await get(url), "html.parser", from_encoding="utf8")


async def getFeeds(mode=None, page=1, url=None):
    if not url:
        url = FeatureUrl.format(mode, page)
    #    print(42, url)
    data = await soup(url)
    #    print(data.contents)
    movies = []
    dattt = data.find("div", "entry-content") or data.find("div", "featured")
    if not dattt:
        return []
    for item in dattt.find_all("li"):
        atag = item.find("a")
        img = atag.find("img")
        if not img:
            continue
        movies.append(
            {
                "title": atag.get("title"),
                "id": atag.get("href").split("/")[-2],
                "image": img.get("src"),
            }
        )
    return movies


async def parsePage(id: str):
    url = f"https://5movierulz.vet/{id}"
    content = await soup(url)
    entryCOB = content.find("div", "entry-content")
    descb = entryCOB.find_all("p")
    data = {}
    data["image"] = entryCOB.find("img").get("src")
    title = descb[0].text
    extra = (
        descb[1]
        .text.replace("<br/>", "\n")
        .strip()
        .replace("<p>", "")
        .replace("</p>", "")
        .split("\n")
    )
    description = descb[2].text.replace("<p>", "").replace("</p>", "")
    data["Description"] = description
    for line in extra:
        eaa = line.split(":")
        try:
            data[eaa[0]] = eaa[1].strip()
        except:
            pass
    data["title"] = title
    urlBox = {}
    for box in descb:
        if not box.find("strong"):
            continue
        service = box.find("strong").text.split("–")[-1].strip()
        url = box.find("a")
        if not url:
            continue
        url = url.get("href")
        urlBox[service] = url
    from pprint import pprint

    return data, urlBox


pageBar = s.AppBar(
    title="MovieMax",
    left_icon="https://f004.backblazeb2.com/file/switch-bucket/28ebc216-ac94-11ee-a0fc-d41b81d4a9ef.png",
    secondary_icon="https://f004.backblazeb2.com/file/switch-bucket/081ef44e-ac95-11ee-ad6b-d41b81d4a9ef.png",
)


app = Client(
    BOT_TOKEN
).set_bot_commands(
    [
        BotCommand("start", "Get Start message", True),
        BotCommand("search", "Search Movies", True),
    ]
)




async def makeShortLink(url):
    async with ClientSession() as ses:
        async with ses.get(
            f"https://api.shareus.io/easy_api?key={ADS_TOKEN}&link={url}"
        ) as res:
            return (await res.read()).decode()


if ADS_TOKEN and not (SHARE_URL and RESOLVED_URL):
    RESOLVED_URL = f"https://switch.click/{app.user.user_name}"
    SHARE_URL = app.run(makeShortLink(RESOLVED_URL))

@app.on_command("start")
async def onStart(ctx: BotContext[CommandEvent]):
    m = ctx.event.message
    await m.reply_text(
        f"🎬 Hi *{m.user.name}*, I am {ctx.user.name}!\n\n🎦 Click below button to open App!",
        inline_markup=InlineMarkup(
            [[InlineKeyboardButton("Open Movie Max 🎦", callback_data="openapp")]]
        ),
    )


PageMaker = {
    "Hollywood": "https://5movierulz.vet/category/hollywood-movie-2023/",
    "Bollywood": "bollywood-movie-free",
    "Malayalam": "malayalam-movie-online",
    "Telugu": "telugu-movie",
    "Tamil": "tamil-movie",
    "Comedy": "https://5movierulz.vet/tag/comedy/",
    "Romance": "https://5movierulz.vet/tag/romance/",
    "Biography": "https://5movierulz.vet/tag/biography/",
}


async def createHome():
    newBox = {}

    async def fetch(y, index):
        isUrl = "http" in y[1]
        mode = y[1] if not isUrl else None
        newBox[y[0]] = {
            "url": await getFeeds(mode, url=y[1] if isUrl else None),
            "index": index,
        }

    await asyncio.gather(
        *[fetch(y, index) for index, y in enumerate(PageMaker.items())]
    )
    return {x: y["url"] for x, y in sorted(newBox.items(), key=lambda x: x[1]["index"])}


@app.on_callback_query(regexp("play(.*)"))
async def openAPP(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.message
    data = ctx.event.callback_data.split("_")[-1]
    details, urlBox = await parsePage(data)
    print(data, ctx.event.action_by_id)
    comps = []
    url = None
    for y in ["Streamtape", "Streamwish", "Mixdrop"]:
        if urlBox.get(y):
            url = await getLink(urlBox[y])
            break
    if not url:
        comps.append(
            s.Text("ERROR: Streamable link not found!", s.TextSize.SMALL)
        )
    else:
        comps.append(s.Embed(url,
                             landscape=True,
                            allow_navigation=False))

    await ctx.event.answer(
        callback=s.AppPage(
            components=comps,
        ), new_page=True
    )


def checkUser(user):
    if not (ADS_TOKEN or (RESOLVED_URL and SHARE_URL)):
        return True
    if time := tokenCache.get(user):
        diff = (dt.now() - dt.fromtimestamp(time)).total_seconds() // (3600)
        if diff < 24:
            return True
    return False




@app.on_callback_query(regexp("navigate"))
async def navig(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.message
    url = ctx.event.details.get("url")
    if url.lower() != RESOLVED_URL.lower():
        return
    await ctx.event.answer("Verified!", show_alert=True)
    tokenCache[ctx.event.action_by_id] = dt.now().timestamp()
    data = ctx.event.callback_data.split("|")[-1]
    await showMovie(ctx, data[-1])



@app.on_callback_query(regexp("wv"))
async def Movie(ctx: BotContext[CallbackQueryEvent], movieId=None):
    await ctx.event.answer(
        callback=AppPage(
            components=[Embed(ctx.event.callback_data.split("|")[-1], full_screen=True)]
        ),
        new_page=True,
    )


@app.on_callback_query(regexp("m(.*)"))
async def showMovie(ctx: BotContext[CallbackQueryEvent], movieId=None):
    m = ctx.event.message
    data = movieId or ctx.event.callback_data.split("|")[-1]
    details, urlBox = await parsePage(data)
    comps= []
    comps.append(s.Text(details["title"], s.TextSize.SMALL))
    comps.append(
        s.Image(url=details["image"]),
    )
    
    verified = checkUser(ctx.event.action_by_id)

    bts = []
    if verified:
        bts.append(
            Button(
                "Play",
                icon="https://img.icons8.com/?size=256&id=nMSSSpYre8pz&format=png",
                callback_data=f"play_{data}",
            )
        )
        print(urlBox)
        if ul := urlBox.get("Download"):
            bts.append(
                Button(
                    f"Download",
                    callback_data=f"wv|{ul}",
                )
            )
    else:
        bts.append(Button(f"Verify to Unlock", callback_data=f"validate|{data}"))
    comps.append(ButtonGroup(bts))

    for x, y in list(details.items())[:3 if not verified else None]:
        if x == "title" or x == "image":
            continue
        comps.append(s.Text(f"⏺ {x}", s.TextSize.SMALL))
        comps.append(s.Text(y))
    if movieId:
        comps.append(Button("Home", callback_data=f"openapp|fromSearch"))
#    print(verified)
    if not verified:
        comps.append(Text("Please VERIFY BELOW TO open APP!", TextSize.SMALL))
        comps.append(Text("You only need to verify once per 24 hours!"))
        comps.append(
            Embed(
                SHARE_URL,
                fixedBottom=True,
                viewRatio=30,
                enableAds=True,
                allow_navigation=True,
                navigationCallback=f"navigate|{data}",
            )
        )
        comps.append(Button("Expand", callback_data=f"expand|{data}"))

    await ctx.event.answer(callback=s.AppPage(components=comps))


@app.on_callback_query(regexp("expand(.*)"))
async def Movie(ctx: BotContext[CallbackQueryEvent], movieId=None):
    m = ctx.event.message
    data = ctx.event.callback_data.split("|")[-1]
    await ctx.event.answer(
        callback=AppPage(
            components=[
                Embed(
                    SHARE_URL,
                    navigationCallback=f"navigate|{data}",
                    enableAds=True,
                    allow_navigation=True
                )
            ]
        ),
        new_page=True
    )


@app.on_callback_query(regexp("vmore_(.*)"))
async def showCallback(ctx: BotContext[CallbackQueryEvent]):
    cdata = ctx.event.callback_data.split("_")[-1]
    m = ctx.event.message

    url = PageMaker[cdata]
    data = await getFeeds(
        url if "http" not in url else None, url=url if "http" in url else None
    )
    lays, comps = [], []
    lays.append(
        s.Grid(
            title=cdata,
            expansion=s.Expansion.EXPAND,
            options=[
                s.GridItem(
                    title=data["title"],
                    media=data["image"],
                    selective=True,
                    callback_data=f"m|{data['id']}",
                )
                for data in data
            ],
        ),
    )
    await ctx.event.answer(callback=s.AppPage(components=comps, layouts=lays))


@app.on_callback_query(regexp("searchMovie"))
async def showCallback(ctx: BotContext[CallbackQueryEvent]):
    #    await ctx.event.message.send(ctx.event.callback_data)
    m = ctx.event.message
    query = ctx.event.details.get("searchQuery")
    if not query:
        return await ctx.event.answer("Provide a query to search", show_alert=True)
    lays, comps = [], [
        s.SearchBar(
            placeholder="Search Movies",
            callback_data="searchMovie",
            label="Find the content you want!",
        )
    ]
    details = await getFeeds(url="https://5movierulz.vet/?s=" + query)
    lays.append(
        s.Grid(
            title=f"Search Results for {query}...",
            expansion=s.Expansion.EXPAND,
            options=[
                s.GridItem(
                    title=data["title"],
                    media=data["image"],
                    selective=True,
                    callback_data=f"m|{data['id']}",
                )
                for data in details
            ],
        ),
    )
    await ctx.event.answer(callback=s.AppPage(components=comps, layouts=lays))


def splitList(lis, n):
    res = []
    while lis:
        res.append(lis[:n])
        lis = lis[n:]
    return res


async def searchMovie(
    ctx: BotContext[CommandEvent], query: str, offset: int = 0, from_callback=False
):
    m = ctx.event.message
    if not from_callback:
        s = await m.reply_text("🔍 Searching Movies")
    wordLength = len(query)
    results = []
    while len(results) < 10 and wordLength:
        for movie in await getFeeds(
            url="https://5movierulz.bond/?s=" + query[:wordLength]
        ):
            if movie not in results:
                results.append(movie)
        wordLength -= 1
    size = 8
    splitOut = splitList(results, size)
    splitt = splitOut[offset]
    message = f"""🍿 *Total Results:* {len(results)}\n__{ctx.event.user.name}__ searched for __{query}__"""
    mkup = [
        [InlineKeyboardButton(i["title"], callback_data=f"splay|{i['id']}")]
        for i in splitt
    ]
    bts = []
    try:
        splitOut[offset - 1]
        bts.append(
            InlineKeyboardButton("🔙 Previous", callback_data=f"sct|{query}|{offset-1}")
        )
    except IndexError:
        pass
    try:
        splitOut[offset + 1]
        bts.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"sct|{query}|{offset+1}")
        )
    except IndexError:
        pass
    if bts:
        mkup.append(bts)
    if from_callback:
        await m.edit_text(message, inline_markup=InlineMarkup(mkup))
    else:
        await m.reply_text(message, inline_markup=InlineMarkup(mkup))
        await s.delete()


@app.on_callback_query(regexp("splay"))
async def showCallback(ctx: BotContext[CallbackQueryEvent]):
    movieID = ctx.event.callback_data.split("|")[-1]
    #    await openAPP(ctx)
    #   print(movieID)
    await showMovie(ctx, movieID)


@app.on_callback_query(regexp("sct"))
async def showCallback(ctx: BotContext[CallbackQueryEvent]):
    query, offset = ctx.event.callback_data.split("|")[1:]
    await searchMovie(ctx, query, int(offset), from_callback=True)


@app.on_command("search")
async def onSearch(ctx: BotContext[CommandEvent]):
    if not ctx.event.params:
        return await ctx.event.message.reply_text(f"🍿 Provide movie name to search!")
    await searchMovie(ctx, ctx.event.params)


@app.on_callback_query(regexp("search$"))
async def showCallback(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.message
    lays, comps = [], [
        s.SearchBar(
            placeholder="Search Movies",
            callback_data="searchMovie",
            label="Find the content you want!",
        )
    ]
    await ctx.event.answer(callback=s.AppPage(components=comps, layouts=lays))



@app.on_callback_query(regexp("openapp"))
async def openAPP(ctx: BotContext[CallbackQueryEvent]):
    m = ctx.event.message
    homePage = await createHome()
    lays, comps = [], [
        s.SearchHolder(placeholder="Search Movies", callback_data="search"),
    ]
    lays.append(
        s.Carousel(
            [
                s.Image(
                    "https://s3.ap-southeast-1.amazonaws.com/images.deccanchronicle.com/dc-Cover-aa8d99rcqfd4kq9e5gi8bogu54-20231101224316.Medi.jpeg",
                    "m|12th-fail-2023-hdrip-hindi-full-movie-watch-online-free",
                ),
                s.Image(
                    "https://th.bing.com/th/id/OIP.E5aAKgUke1ezPGQX89e96QHaEK?w=303&h=180&c=7&r=0&o=5&pid=1.7",
                    "m|hi-papa-2023-hdrip-hindi-full-movie-watch-online-free",
                ),
                s.Image(
                    "https://th.bing.com/th?id=OIF.zx1oFNeE%2bJs20cFoWIFWdw&rs=1&pid=ImgDetMain",
                    "m|salaar-cease-fire-part-1-2023-dvdscr-hindi-full-movie-watch-online-free",
                ),
                s.Image(
                    "https://autowithsid.in/wp-content/uploads/2023/06/Animal-Upcoming-Ranbir-Kapoor-Movie-2023.jpg",
                    "m|animal-2023-v2-dvdscr-hindi-full-movie-watch-online-free",
                ),
                s.Image(
                    "https://ticketsearch.in/wp-content/uploads/2023/09/dunki-ticket.webp",
                    "m|dunki-2023-dvdscr-hindi-full-movie-watch-online-free",
                ),
            ]
        ),
    )
    for lay, cards in homePage.items():
#        print(cards)
        if not cards:
            continue
        lays.append(
            s.Grid(
                lay,
                horizontal=True,
                expansion=s.Expansion.EXPAND,
                size=3,
                right_image="https://f004.backblazeb2.com/file/switch-bucket/9c99cba4-a988-11ee-8ef4-d41b81d4a9ef.png",
                image_callback=f"vmore_{lay}",
                options=[
                    s.GridItem(
                        title=data["title"][:15],
                        media=data["image"],
                        selective=True,
                        callback_data=f"m|{data['id']}",
                    )
                    for data in cards[:10]
                ],
            )
        )
    await ctx.event.answer(callback=s.AppPage(components=comps, layouts=lays))


def clean24HOURS():
    for user, time in list(tokenCache.items()):
        diff = (dt.now() - dt.fromtimestamp(time)).total_seconds() // 3600
        if diff > 24:
            del tokenCache[user]


every(1).hour.do(clean24HOURS)

app.run()
