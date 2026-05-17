from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, datetime, random

ITEMS = []

HTML = """<!DOCTYPE html>
<html>
<head>
<title>MY SUPER COOL WEBSITE!!!!</title>
<style>
  body {{
    background-color: #ff00ff;
    background-image: repeating-linear-gradient(45deg, #ff0000 0px, #ff0000 10px, #ffff00 10px, #ffff00 20px);
    font-family: "Comic Sans MS", cursive;
    color: lime;
    text-align: center;
    margin: 0;
    padding: 20px;
  }}
  h1 {{
    font-size: 72px;
    color: red;
    text-shadow: 5px 5px 0px blue, -5px -5px 0px yellow;
    animation: blink 0.5s step-start infinite;
    transform: rotate(-3deg);
    display: inline-block;
  }}
  @keyframes blink {{
    50% {{ opacity: 0; }}
  }}
  marquee {{
    background: black;
    color: cyan;
    font-size: 24px;
    border: 5px dashed red;
    padding: 5px;
  }}
  .box {{
    background: rgba(0,0,0,0.6);
    border: 8px groove orange;
    margin: 20px auto;
    padding: 15px;
    width: 600px;
    box-shadow: 20px 20px 0px purple;
  }}
  input[type=text] {{
    background: black;
    color: lime;
    border: 3px solid cyan;
    font-family: "Comic Sans MS", cursive;
    font-size: 18px;
    padding: 5px;
    width: 300px;
  }}
  button {{
    background: red;
    color: yellow;
    font-family: "Comic Sans MS", cursive;
    font-size: 20px;
    font-weight: bold;
    border: 4px outset orange;
    padding: 10px 20px;
    cursor: pointer;
    text-transform: uppercase;
    transform: skewX(-10deg);
  }}
  button:hover {{ background: blue; color: white; }}
  .item {{
    background: {item_bg};
    color: white;
    border: 3px solid yellow;
    margin: 5px;
    padding: 8px;
    font-size: 20px;
    text-align: left;
    transform: rotate({rot}deg);
  }}
  .counter {{
    font-size: 48px;
    color: yellow;
    text-shadow: 3px 3px black;
  }}
  .time {{
    color: cyan;
    font-size: 14px;
    font-style: italic;
  }}
  img {{ width: 80px; }}
  .corner {{
    position: fixed;
    font-size: 60px;
  }}
  .tl {{ top: 0; left: 0; }}
  .tr {{ top: 0; right: 0; }}
  .bl {{ bottom: 0; left: 0; }}
  .br {{ bottom: 0; right: 0; }}
</style>
</head>
<body>
<div class="corner tl">&#x1F525;</div>
<div class="corner tr">&#x1F4A5;</div>
<div class="corner bl">&#x2728;</div>
<div class="corner br">&#x1F31F;</div>

<marquee scrollamount="10">*** WELCOME TO MY TOTALLY AWESOME TO-DO LIST APP v1.0 FINAL FINAL v3 ***&nbsp;&nbsp;&nbsp;
MADE BY A GENIUS&nbsp;&nbsp;&nbsp;*** DO NOT STEAL ***&nbsp;&nbsp;&nbsp;BEST VIEWED IN INTERNET EXPLORER 6 ***</marquee>

<h1>~~~ MY TODO APP ~~~</h1>

<p class="time">Today is: {date} &nbsp;|&nbsp; Server uptime: UNKNOWN &nbsp;|&nbsp; Browser: WHO KNOWS</p>

<div class="box">
  <p class="counter">YOU HAVE {count} TASKS!!!</p>

  <form method="POST" action="/add">
    <input type="text" name="item" placeholder="type ur task here..." maxlength="100" />
    <br/><br/>
    <button type="submit">&#x2714; ADD IT NOW CLICK HERE &#x2714;</button>
  </form>
</div>

<div class="box">
  <h2 style="color:yellow;font-size:36px;">&#x1F4CB; TASK LIST &#x1F4CB;</h2>
  {items_html}
</div>

<div class="box">
  <form method="POST" action="/clear">
    <button type="submit" style="background:darkred;">&#x274C; DELETE ALL TASKS (DANGER!!!) &#x274C;</button>
  </form>
</div>

<marquee direction="right" scrollamount="5" style="color:red;font-size:30px;">
  &#x2605; &#x2605; &#x2605; THANKS FOR VISITING MY SITE &#x2605; &#x2605; &#x2605;
</marquee>

<p style="color:white;font-size:10px;">
  &copy; {year} MY WEBSITE &bull; All Rights Reserved &bull; Do Not Copy &bull;
  Best viewed at 800x600 resolution &bull; Requires Flash Player 9.0
</p>

</body>
</html>"""

COLORS = ["#cc0000","#006600","#000099","#884400","#660066","#008888"]

def render():
    items_html = ""
    for i, item in enumerate(ITEMS):
        rot = (i % 3) - 1
        bg = COLORS[i % len(COLORS)]
        items_html += f'<div class="item" style="background:{bg};transform:rotate({rot}deg)">{"&#x2705;" if i%2==0 else "&#x274C;"} {i+1}. {item}</div>\n'
    if not items_html:
        items_html = '<p style="color:yellow;font-size:24px;">NO TASKS!!! ADD SOME!!! WHY ARE YOU SO LAZY!!!</p>'
    return HTML.format(
        count=len(ITEMS),
        items_html=items_html,
        date=datetime.date.today().strftime("%A, %B %d %Y"),
        year=datetime.date.today().year,
        item_bg=COLORS[0],
        rot=0,
    )

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(render().encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(body)

        if self.path == "/add":
            item = params.get("item", [""])[0].strip()
            if item:
                ITEMS.append(item)
        elif self.path == "/clear":
            ITEMS.clear()

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # silence access logs

if __name__ == "__main__":
    port = 8080
    print(f"Server running at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    HTTPServer(("", port), Handler).serve_forever()
