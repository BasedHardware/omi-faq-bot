# Omi Discord Bot

## How to Run

```bash
 # package manager
 uv 
````

### Installation

* Clone the repository
* Create a virtual environment:

  ```bash
  uv venv env
  ```
* Activate the virtual environment:

  ```bash
  source env/bin/activate
  ```
* Install dependencies:

  ```bash
  uv pip install -r requirements.txt
  ```

### Configuration

Create a `.env` file in the project root and add your bot token:

```env
TOKEN=your_bot_token
```

### Running the Bot

```bash
# Run the bot
python main.py

# Run with auto-restart on file changes
watchmedo auto-restart --recursive --pattern="*.py" -- python main.py
```

### Indexing the Knowledge Base

In your Discord server, run:

```
$index
```

---

## Commands

* `$index` — Indexes the `faq.json` file
* `$reload_index` — Reloads the BM25 index
* `$sync` — Syncs slash commands

---

## Running Indexer Tests

```bash
python test/indexer_test.py
```
