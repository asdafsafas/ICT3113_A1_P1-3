# ICT3113 Assignment 1: Ticket Triage (Team P1-3)

A ticket classification service for a financial complaints desk, running on CPU-only models in Docker, plus the tests that decide which model the client should deploy.

- **Who does what and when:** [docs/team-plan.md](docs/team-plan.md)
- **All project docs** (setup, architecture, testing playbooks): [docs/README.md](docs/README.md)
- **Quick start** (needs Docker Desktop): `cp .env.example .env`, then `docker compose up -d --build`, then `python scripts/pull_models.py`. Details in [docs/setup.md](docs/setup.md).

---

## Labelling the golden set

Right now we're building the **golden test set** (Step 1 of the brief): 200 tickets labelled by hand, which we'll later use to measure how accurate each model is. Each ticket is labelled by **at least two people working independently**.

## Who labels what

| Group | Labellers | Tickets | Rows to choose in the app |
|---|---|---|---|
| A | Zong Han, Ridwan | 1st–100th | **3000–3099** |
| B | Tze Han, Kannan, Natalie | 101st–200th | **3100–3199** |

Everyone in a group labels **all 100 tickets** in their range.

## Setup (about 5 minutes)

You need **Python 3.7 or newer**. Nothing else to install.

1. **Get the code.** Accept the GitHub invite, then:
   ```
   git clone https://github.com/asdafsafas/ICT3113_A1_P1-3.git
   cd ICT3113_A1_P1-3
   ```
   (No git? On the repo page, click **Code → Download ZIP** and unzip it.)

2. **Start the labeller:**
   ```
   python labeler/labeler.py
   ```
   If `python` isn't recognised, try `py` (Windows) or `python3` (Mac).

3. **Open http://localhost:8765** in your browser.

4. **Enter your name exactly as below, and choose your group's rows** from the "Rows you're labelling" list. Your labels are saved under this name, so use the same one every time:

   | Person | Name to enter |
   |---|---|
   | Zong Han | `Zong_Han` |
   | Ridwan | `Ridwan` |
   | Tze Han | `Tze_Han` |
   | Kannan | `Kannan` |
   | Natalie | `Natalie` |

   The app remembers your rows. You can change them any time with the **Rows** menu at the top of the page (it also has a custom range), but stick to your group's rows.

**Keep the terminal window open while you label.** Closing it stops the app. Your progress stays saved; run the same command again to continue.

## How to label

For each ticket:

1. **Read the narrative.** Greyed-out `XXXX` text is personal information the CFPB (the US Consumer Financial Protection Bureau) removed before publishing; skip over it.
2. **Pick one category** (click it, or press **1–8**). Hover over a category to see its definition.
3. **"Also fits"** (optional): if the ticket could reasonably belong to a second category, pick it here. This helps us later when we compare labels.
4. **Reasoning:** write a short note on why you chose that category, especially when you're unsure. For example: *"Paid collection still on report after 7 years; wants it removed, so Credit reporting."*
5. **Save & next** (or **Ctrl+Enter**).

**Other controls:**
- **Save & stop:** saves your work and lets you close the tab. When you come back, you continue from where you stopped.
- **← / →**, **Prev / Next**, the row squares at the top, or **Row #** let you go back and change any label. Every save overwrites your previous answer for that ticket.
- **A− / A+** changes the text size.

**About "None / unclear" (key 8):** use it when a ticket genuinely fits none of the 7 categories or is too vague to decide, and explain why in the reasoning. It isn't a final answer; we decide those tickets together afterwards.

## Rules (important for our marks)

The brief checks that our labels are **independent** and weren't influenced by any model. Breaking these rules weakens the golden set, and the marker will look closely at it.

1. **Don't discuss tickets with anyone, including the others in your group, until everyone in the group has finished.** No comparing, no screenshots, no "what did you put for row 3042?".
2. **Don't ask ChatGPT, Claude or any other AI which category a ticket belongs to.** The models we're testing are AIs; if our labels copy an AI's answers, our accuracy results become meaningless. Looking up what a term or company is (e.g. "what is FCRA?", "who is Navient?") is fine.
3. **Use only the definitions in the app** (from [labeler/protocol.json](labeler/protocol.json), currently **v0.1**). Don't edit that file. If a definition is missing or unclear, **note it in your reasoning**; we'll fix the protocol together after this round.
4. **Don't look at the original labels** in the spreadsheet (the `source_label` column). They're known to be unreliable, and they'd bias you. The app hides them on purpose.

## When you're done

Your labels are saved to `labeler/labels/labels_<YourName>.csv` (e.g. `labels_Ridwan.csv`). They're deliberately **not tracked by git**, so nobody can see anyone else's labels early.

1. Check that the progress bar reads **100 / 100 labelled**.
2. **Send your CSV file to Zong Han privately** (Telegram, Teams or email). Don't post it in the group chat.
3. Once **everyone in a group** has sent their file, Zong Han commits them to the repo.

## What happens next

1. **Compare:** we calculate the agreement statistics (Cohen's kappa for each pair of labellers, Fleiss' kappa for group B's three) and list every ticket where the labels differ.
2. **Resolve:** each group meets and agrees a final label for each disagreement, recording why.
3. **Revise the protocol:** where a disagreement shows a missing rule, we add it to the protocol as v0.2 and record the change.
4. **Freeze:** the agreed labels become the golden set, which is committed **before any model is tested on it**. Every test and benchmark run waits for this step.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` is not recognised | Use `py labeler/labeler.py …` (Windows) or `python3 labeler/labeler.py …` (Mac). If neither works, install Python from python.org. |
| `Address already in use` | The app is probably already running in another terminal. Use that one, or add `--port 8766` and open http://localhost:8766. |
| The page shows someone else's name | Click **switch** next to the name and enter yours. |
| The page shows 200 tickets, or the wrong rows | Pick your group's rows from the **Rows** menu at the top of the page. |
| I labelled a ticket outside my range | That's fine, it doesn't hurt anything. Just make sure every ticket in your range is labelled. |
