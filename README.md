# Brady Golomb — portfolio site

A home page, nine project pages, and two interactive simulators. Plain HTML, CSS, and JavaScript, with no build step and no frameworks. Open `index.html` in a browser to preview it locally.

Live at **https://bradygolomb.github.io**

## What's in this folder

| File | What it is |
|---|---|
| `index.html` | Home: hero, project index, about |
| `bike-adapter.html` | Sheet 01: Prosthetic Bike Adapter (Penn ADAPT) |
| `bungee.html` | Sheet 02: Rubber-Band Bungee Cord (MEAM 3470) |
| `rocket.html` | Sheet 03: Bottle Rocket Trajectory Model (MEAM 2480) |
| `vex-robot.html` | Sheet 04: VEX Competition Robot (Carroll Robotics) |
| `running-robot.html` | Sheet 05: Running Form Robot (personal project) |
| `running-robot-v2.html` | Sheet 06: Running Form Robot v2 (in development, links to the GitHub repo) |
| `wound-care-app.html` | Sheet 07: Delta Wound App (One Health Partners) |
| `emr-podcast.html` | Sheet 08: Wound Care Discharge System (One Health Partners) |
| `wind-up-toy.html` | Sheet 09: Wind-Up Toy Teardown (Penn Engineering) |
| `bungee-sim.html` | Interactive bungee drop simulator, linked from `bungee.html` |
| `rocket-sim.html` | Interactive rocket launch simulator, linked from `rocket.html` |
| `bungee_design_model.py` | Bungee design model (Python, standard library only) |
| `bungee_accel_logger.ino` | Arduino accelerometer logger for the bungee drop |
| `rocket_flight_model.py` | Rocket flight model and inverse solver (needs numpy, scipy, matplotlib) |
| `style.css` | All styling for the project pages and home page |
| `resume.pdf` | Linked from the nav, the About section, and every page footer |
| `images/` | Project photos and figures |

The two simulators carry their own styles and run fully in the browser. They don't use `style.css`.

## Images

Each page expects these files:

| Page | Files |
|---|---|
| bike-adapter | `images/bike-adapter-01.png` `-02.png` `-03.png` |
| bungee | `bungee-01.png` `bungee-02.png` (these sit in the main folder, not `images/`) |
| rocket | `images/rocket-01.jpg` `images/rocket-02.jpg` |
| vex-robot | `images/vex-01.png` `images/vex-02.png` |
| running-robot | none yet: this page needs photos |
| running-robot-v2 | none yet: add Gazebo screenshots or an `rqt_plot` capture as the build progresses |
| wound-care-app | `images/wound-app-01.png` `-02.png` `-03.png` |
| emr-podcast | `images/emr-01.png` `-02.png` `-03.png` |
| wind-up-toy | `images/wind-up-01.png` `-02.png` `-03.png` |

To add a photo, save it into `images/`, then copy an existing `<figure>` block on that page, change the `src`, write a real `alt` description (it matters for accessibility and search), and bump the figure number in the caption. Resize anything over about 2000 px wide first, or pages will load slowly.

## Adding a new project

1. Copy an existing project page (for example `bungee.html`) and rename it.
2. Edit the eyebrow (`Sheet NN of NN`), title, standfirst, title block, and sections.
3. Add a row for it in the project index in `index.html`, and update the count (`09 projects`).
4. If the sheet total changes, update `Sheet NN of NN` on every page, and fix the previous/next links at the bottom of the pages on either side of the new one.

## Updating the site

On the repo page, use **Add file → Upload files** and drop in the changed files. Drag folders in as folders so `images/` keeps its structure. Uploading a file with the same name replaces it. The site redeploys in about a minute.

To change the résumé, upload the new one as `resume.pdf` and every link keeps working.

## Editing text and styling

All text lives directly in the HTML, so search for a sentence and edit it in place. Colors, fonts, and spacing come from the variables at the top of `style.css`, so changing a variable there updates every page at once.

## A custom domain

To use something like bradygolomb.com, buy the domain, then add it under **Settings → Pages → Custom domain** and follow GitHub's DNS instructions. It costs roughly $12 a year.
