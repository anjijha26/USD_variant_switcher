USD Variant Switcher

A simple Houdini Python Panel tool for switching and managing USD variants interactively inside /stage.
The tool lets you load any .usd/.usda/.usdc file, inspect available prims and variant sets, and apply or switch between variants directly from the UI.

✨ Features

📂 Load any USD file (.usd, .usda, .usdc) into /stage.

🔎 Auto-detects prims and their variant sets.

🎚 Easy dropdowns for Prim → Variant Set → Variant Option.

⚡️ Applies selected variants by creating Set Variant LOPs dynamically.

🌀 Smart duplicate prevention: if the same variant already exists, it just reuses that node.

🧹 Clear Variants button to remove all variant_applier_* nodes and reset the stage.

👀 Always updates the viewport automatically (sets display flag on the active node).
