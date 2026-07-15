import os
import re

LOG_FILE = 'build.log'
TEMPLATE_FILE = 'README.template.md'
OUTPUT_FILE = 'README.md'

apps_data = {}
current_app = None
current_patch_file = "Unknown"

def clean_terminal_formatting(text):
    """Removes ANSI color codes and timestamps from the log lines."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    text = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+', '', text)
    return text.strip()

# 1. Parse the log file line by line
try:
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            clean_line = clean_terminal_formatting(line)
            
            # Detect Patch Bundle Version (e.g., [+] Getting 'patches-1.34.0.mpp' from...)
            if "[+] Getting '" in clean_line and "' from" in clean_line:
                match = re.search(r"\[\+\] Getting '(.*?)' from", clean_line)
                if match:
                    current_patch_file = match.group(1)

            # Detect App Name & Exact App Version (e.g., [+] Choosing version '21.26.360' for 'YouTube')
            elif "[+] Choosing version '" in clean_line:
                match = re.search(r"Choosing version '(.*?)' for '(.*?)'", clean_line)
                if match:
                    app_version = match.group(1)
                    app_name = match.group(2)
                    current_app = app_name
                    
                    if current_app not in apps_data:
                        apps_data[current_app] = {
                            'version': app_version,
                            'patch_file': current_patch_file,
                            'applied': [],
                            'excluded': []
                        }
                    else:
                        apps_data[current_app]['version'] = app_version
                        apps_data[current_app]['patch_file'] = current_patch_file

            # Fallback just to ensure the app name is caught if version line is missing
            elif "[+] Building '" in clean_line:
                app_name = clean_line.split("[+] Building '")[1].split("'")[0].strip()
                current_app = app_name
                if current_app not in apps_data:
                    apps_data[current_app] = {
                        'version': "Unknown (Check Releases)",
                        'patch_file': current_patch_file,
                        'applied': [],
                        'excluded': []
                    }
                    
            # Detect Applied Patches
            elif current_app and "INFO: Applied: " in clean_line:
                patch = clean_line.split("INFO: Applied: ")[1].strip()
                if patch not in apps_data[current_app]['applied']:
                    apps_data[current_app]['applied'].append(patch)
                    
            # Detect Manually Excluded Patches
            elif current_app and "INFO: Skipping disabled: " in clean_line:
                patch = clean_line.split("INFO: Skipping disabled: ")[1].strip()
                if not patch.endswith("(default)"):
                    if patch not in apps_data[current_app]['excluded']:
                        apps_data[current_app]['excluded'].append(patch)
                        
except FileNotFoundError:
    print(f"Error: {LOG_FILE} not found. Did the workflow combine them properly?")
    exit(1)

# 2. Format the parsed data into Markdown
apps_md = ""
for index, (app_name, data) in enumerate(apps_data.items(), start=1):
    applied = data['applied']
    excluded = data['excluded']
    
    apps_md += f"<details>\n<summary><b>{index}. {app_name}</b></summary>\n\n"
    
    # Add Versions
    apps_md += f"* **App Version:** `{data['version']}`\n"
    apps_md += f"* **Patch Bundle:** `{data['patch_file']}`\n\n"
    
    # Add Applied Patches
    apps_md += f"* **Applied Patches ({len(applied)}):**\n"
    if applied:
        for patch in sorted(applied):
            apps_md += f"  * `{patch}`\n"
    else:
        apps_md += "  * `No patches detected.`\n"
        
    # Add Excluded Patches
    if excluded:
        apps_md += f"\n* **Excluded Patches ({len(excluded)}):**\n"
        for patch in sorted(excluded):
            apps_md += f"  * `{patch}`\n"
            
    apps_md += "</details>\n\n"

# 3. Inject into README template
try:
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()
except FileNotFoundError:
    print(f"Error: {TEMPLATE_FILE} not found.")
    exit(1)

final_readme = template.replace('{{APPS_LIST}}', apps_md.strip())

# 4. Save the final README
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(final_readme)

print("README.md successfully updated with full version and patch tracking!")
