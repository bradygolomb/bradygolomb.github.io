# Brady Golomb — portfolio site

Seven pages: a home page and one page per project. Plain HTML and CSS, no build step,
no frameworks. Open `index.html` in a browser to preview it locally.

```
index.html              home — hero, project index, about
wound-care-app.html     01  One Health Partners
emr-podcast.html        02  One Health Partners
bike-adapter.html       03  Penn ADAPT
vex-robot.html          04  Carroll Robotics
running-robot.html      05  personal project
wind-up-toy.html        06  Penn Engineering
style.css               all styling for every page
resume.pdf              linked from the nav and About section
images/                 project photos go here
```

---

## 1. Add your images

Every project page has placeholder boxes where photos go. Each one shows the exact
filename it expects, and directly above it in the HTML there's a comment with the
line to paste in.

Find a placeholder like this:

```html
<!-- IMAGE: replace this block with →  <img src="images/bike-adapter-01.jpg" alt="..."> -->
<div class="img-slot img-slot-wide"><span>images/bike-adapter-01.jpg</span></div>
```

Save your photo into `images/` with that filename, then delete the `<div>` line and
replace it with the `<img>` line from the comment. Write a real `alt` description —
it matters for accessibility and for search.

Filenames expected:

| Page | Files |
|---|---|
| wound-care-app | `wound-app-01.jpg` `wound-app-02.jpg` `wound-app-03.jpg` |
| emr-podcast | `emr-01.jpg` `emr-02.jpg` `emr-03.jpg` |
| bike-adapter | `bike-adapter-01.jpg` `bike-adapter-02.jpg` `bike-adapter-03.jpg` |
| vex-robot | `vex-01.jpg` `vex-02.jpg` `vex-03.jpg` |
| running-robot | `running-robot-01.jpg` `running-robot-02.jpg` `running-robot-03.jpg` |
| wind-up-toy | `wind-up-01.jpg` `wind-up-02.jpg` `wind-up-03.jpg` |

You can add more than three per page — copy an existing `<figure>` block and bump
the figure number. Pull the CAD renders from your original Google Slides at full
resolution rather than from the PDF; the PDF versions are compressed.

Resize anything over ~2000px wide before uploading, or pages will load slowly.

## 2. Replace the résumé

`resume.pdf` is currently your March 2026 version. Swap in the updated one — same
filename, and every link keeps working.

---

## 3. Put it online with GitHub Pages

Free, permanent, and gives you `bradygolomb.github.io`.

1. Sign in at github.com. If your username isn't already `bradygolomb`, you can
   change it in Settings → Account.
2. Click **+** → **New repository**. Name it exactly `bradygolomb.github.io`
   (substituting your username). Set it to **Public**. Don't add a README —
   this folder has one.
3. On the empty repo page, click **uploading an existing file**.
4. Drag in everything from this folder, including the `images` folder. Click
   **Commit changes**.
5. Wait about a minute, then visit `https://bradygolomb.github.io`.

If you name the repo something else — `portfolio`, say — the site still works, but
it lives at `username.github.io/portfolio` and you'll need to turn Pages on manually
under Settings → Pages → Source → `main` branch.

### Updating it later

Edit files locally, then on the repo page use **Add file → Upload files** and drop in
the changed ones. It redeploys in under a minute.

### A custom domain

If you'd rather have `bradygolomb.com`, buy the domain, then in Settings → Pages add
it under Custom domain and follow GitHub's DNS instructions. Roughly $12 a year.

---

## Editing the text

All copy is written directly in the HTML — no CMS, no data files. Search for a
sentence and edit it in place. The colors, fonts, and spacing all come from the
variables at the top of `style.css`, so changing `--select` there changes every
accent on the site at once.
