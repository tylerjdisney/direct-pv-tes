# Start here (delete this file when you're set up)

Welcome to the Dept of Makers project template. This takes about 20 minutes.

## 1. Set up
- [ ] Rename the repo to something short and lowercase, like `solar-shower`.
- [ ] Go to **Settings → Pages** and set **Source** to **GitHub Actions**.
- [ ] In `mkdocs.yml`, replace `PROJECT NAME`, `YOUR NAME`, and `REPO-NAME`.
- [ ] Go to the repo's main page, click the gear next to **About**, and add the topics
      `mars-college`, `dept-of-makers`, `mars-2027`, and `open-hardware`.
      Paste your website link there too.

## 2. Fill in the docs
| File | What goes in it |
|---|---|
| `README.md` | The front door. One paragraph, one photo, status, links. |
| `BOM.csv` | Every part you bought or used, grouped by subassembly in the `section` column. Give each section an ID prefix (FR-01, WS-01). Edit in any spreadsheet app, save as CSV. |
| `docs/index.md` | Overview: what it is, why it exists, specs. |
| `docs/assembly.md` | Step-by-step build guide with a photo per step. |
| `docs/operation.md` | How to use and maintain it. |
| `docs/design-notes.md` | Calcs, decisions, what you tried and dropped, lessons learned. |
| `cad/source/` | Your native, editable design files. |
| `cad/exports/` | STEP, DXF, PDF drawings, STL. |
| `testing/` | Measurements, logs, test results. |
| `CHANGELOG.md` | What changed in each version. |

## 3. Photos: keep them small
Run this before adding photos (needs Python; see `tools/resize_photos.py` for setup):

```
python tools/resize_photos.py path/to/your/photos
```

It shrinks them to 1600px wide and saves into `docs/images/`. Delete the placeholder
images (`hero.jpg`, `step01-example.jpg`, ...) as you replace them. Name photos by step:
`step04-mount-collector.jpg`.

**Rules:** no single file over 50 MB, no video in the repo (put it on YouTube or
Vimeo and link it), and keep raw photos and big datasets on Zenodo or a drive.
A check runs on every push and warns you about large files.

## 4. Publish
- Every push to `main` rebuilds your website automatically.
  It will be at `https://ORG-NAME.github.io/REPO-NAME/`.
- When you hit a milestone, go to **Releases → Draft a new release** and tag it `v1.0`.
  A PDF of your full documentation is generated and attached to the release automatically.
