with open(r"C:\Users\IT-40126\Documents\August 2026-20261008T011759Z-1-001\August 2026\src\dashboard\generate_dashboard_html.py", "r", encoding="utf-8") as f:
    text = f.read()

target = '<button id="viewToggleBtn" onclick="togglePresentationMode()"'
replacement = """<a href="player_behavior_dashboard.html" class="px-3.5 py-2 rounded-lg bg-cyan-950/60 hover:bg-cyan-900 text-cyan-300 text-xs font-semibold flex items-center gap-2 border border-cyan-700/50 transition" title="Open Player Behavioral Intelligence Deep-Dive">
            <i class="fa-solid fa-gamepad text-cyan-400"></i>
            <span>Behavior Telemetry</span>
          </a>
          <button id="viewToggleBtn" onclick="togglePresentationMode()\""""

if target in text and 'player_behavior_dashboard.html' not in text:
    text = text.replace(target, replacement, 1)
    with open("generate_dashboard_html.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Added cross-dashboard navigation link to generate_dashboard_html.py")
else:
    print("Already present or target not found")

