"""TextLands CLI - Main entry point."""

import re
import sys
import time
import uuid
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

try:
    from . import __version__
    from .client import TextLandsClient
    from .config import (
        get_api_url, set_api_url,
        get_api_key, set_api_key, clear_api_key,
        get_guest_id, set_guest_id,
        get_current_session, set_current_session, clear_current_session,
        is_authenticated,
        get_session_token, set_session_token, clear_session_token,
        get_user_info, set_user_info, clear_user_info,
    )
except ImportError:
    # PyInstaller standalone binary
    from textlands_cli import __version__
    from textlands_cli.client import TextLandsClient
    from textlands_cli.config import (
        get_api_url, set_api_url,
        get_api_key, set_api_key, clear_api_key,
        get_guest_id, set_guest_id,
        get_current_session, set_current_session, clear_current_session,
        is_authenticated,
        get_session_token, set_session_token, clear_session_token,
        get_user_info, set_user_info, clear_user_info,
    )

app = typer.Typer(
    name="textlands",
    help="Play TextLands from your terminal.",
    no_args_is_help=True,
)
console = Console()


def get_client() -> TextLandsClient:
    """Get configured API client."""
    api_url = get_api_url()
    api_key = get_api_key()
    session_token = get_session_token()
    guest_id = get_guest_id()

    # Use session token if available (from magic link auth)
    if session_token:
        user_info = get_user_info()
        # Use user_id as guest_id for session continuity
        player_id = user_info.get("user_id") if user_info else None
        return TextLandsClient(
            base_url=api_url,
            api_key=None,
            guest_id=player_id or guest_id,
        )

    # Generate guest ID if needed and no API key
    if not api_key and not guest_id:
        guest_id = f"cli_{uuid.uuid4().hex[:16]}"
        set_guest_id(guest_id)

    return TextLandsClient(
        base_url=api_url,
        api_key=api_key,
        guest_id=guest_id,
    )


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]{message}[/green]")


def print_narrative(text: str, mood: str = "neutral") -> None:
    """Print narrative text with appropriate styling."""
    mood_styles = {
        "neutral": "white",
        "tense": "yellow",
        "danger": "red",
        "romantic": "magenta",
        "mysterious": "cyan",
        "triumphant": "green",
        "sad": "blue",
    }
    style = mood_styles.get(mood, "white")
    console.print(Panel(text, style=style, padding=(1, 2)))


def print_suggestions(actions: list[str]) -> None:
    """Print suggested actions."""
    if not actions:
        return
    console.print("\n[dim]Suggested actions:[/dim]")
    for i, action in enumerate(actions, 1):
        console.print(f"  [cyan]{i}.[/cyan] {action}")


# =========== Commands ===========

@app.command()
def version():
    """Show version information."""
    console.print(f"TextLands CLI v{__version__}")


@app.command()
def login(
    email: Optional[str] = typer.Argument(None, help="Your email address"),
    api_key: Optional[str] = typer.Option(None, "--key", "-k", help="API key (legacy)"),
):
    """
    Log in to sync progress across devices.

    We'll send a magic link to your email - no password needed.
    """
    # Legacy API key login
    if api_key:
        with TextLandsClient(base_url=get_api_url(), api_key=api_key) as client:
            try:
                session = client.get_session()
                if session.get("is_guest"):
                    print_error("Invalid API key")
                    raise typer.Exit(1)
                set_api_key(api_key)
                print_success(f"Logged in as {session.get('display_name', 'adventurer')}")
            except Exception as e:
                print_error(f"Login failed: {e}")
                raise typer.Exit(1)
        return

    # Magic link flow
    if not email:
        email = Prompt.ask("Enter your email")

    if not email or "@" not in email:
        print_error("Valid email is required")
        raise typer.Exit(1)

    with get_client() as client:
        try:
            # Request device authorization
            result = client.request_cli_auth(email)
            device_code = result["device_code"]
            user_code = result["user_code"]
            verify_url = result["verification_url"]
            expires_in = result["expires_in"]

            console.print(f"\n[bold]Check your email![/bold] We sent a login link to [cyan]{email}[/cyan]")
            console.print(f"\nOr visit: [link={verify_url}]{verify_url}[/link]")
            console.print(f"Code: [bold green]{user_code}[/bold green]\n")

            # Poll for authorization
            with Live(Spinner("dots", text="Waiting for authorization..."), refresh_per_second=4) as live:
                start_time = time.time()
                while time.time() - start_time < expires_in:
                    time.sleep(2)
                    token_result = client.poll_cli_token(device_code)

                    if token_result["status"] == "authorized":
                        # Store session info
                        set_session_token(token_result["session_token"])
                        set_user_info({
                            "user_id": token_result["user_id"],
                            "email": token_result["email"],
                            "display_name": token_result["display_name"],
                        })
                        # Update guest_id to user_id for cross-platform sessions
                        set_guest_id(token_result["user_id"])
                        live.stop()
                        print_success(f"\nLogged in as {token_result.get('display_name') or email}!")
                        console.print("[dim]Your progress now syncs across CLI, web, SMS, and Slack.[/dim]")
                        return

                    if token_result["status"] == "expired":
                        live.stop()
                        print_error("Authorization expired. Try again.")
                        raise typer.Exit(1)

                live.stop()
                print_error("Authorization timed out. Try again.")
                raise typer.Exit(1)

        except Exception as e:
            print_error(f"Login failed: {e}")
            raise typer.Exit(1)


@app.command()
def logout():
    """Log out and clear credentials."""
    clear_api_key()
    clear_session_token()
    clear_user_info()
    clear_current_session()
    print_success("Logged out")


@app.command()
def status():
    """Show current session status."""
    # Show local user info if logged in
    user_info = get_user_info()
    if user_info:
        console.print(f"[green]Logged in as:[/green] {user_info.get('display_name') or user_info.get('email')}")
        console.print(f"[dim]User ID: {user_info.get('user_id')}[/dim]")
        console.print("[dim]Progress syncs across CLI, web, SMS, and Slack[/dim]\n")
    else:
        console.print("[yellow]Playing as guest[/yellow] - use 'textlands login' to sync progress\n")

    with get_client() as client:
        try:
            session = client.get_session()
        except Exception as e:
            print_error(f"Failed to get status: {e}")
            raise typer.Exit(1)

    table = Table(title="Session Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("Player ID", session.get("player_id", "unknown"))
    table.add_row("Synced Account", "Yes" if user_info else "No (guest)")
    table.add_row("Display Name", session.get("display_name", "Adventurer"))

    if session.get("character_name"):
        table.add_row("Character", session["character_name"])
    if session.get("realm_name") or session.get("world_name"):
        table.add_row("Realm", session.get("realm_name") or session.get("world_name"))

    console.print(table)


@app.command()
def realms(
    land: Optional[str] = typer.Option(None, "--land", "-l", help="Filter by land (fantasy, scifi, etc.)"),
    nsfw: bool = typer.Option(False, "--nsfw", help="Include 18+ realms"),
):
    """List available realms to play in."""
    with get_client() as client:
        try:
            if land:
                # Use the legacy endpoint with realm filter
                result = client.list_worlds(realm=land, include_nsfw=nsfw)
                realm_list = result.get("worlds", [])  # API field still "worlds"
            else:
                groups = client.list_worlds_grouped()  # No more include_nsfw param needed
                realm_list = []
                for group in groups:
                    # Use new field names: land, realm_count, realms
                    if group.get("is_locked") and not nsfw:
                        console.print(f"\n[dim]{group['display_name']} ({group['realm_count']} realms) - Age verification required[/dim]")
                        continue
                    console.print(f"\n[bold cyan]{group['display_name']}[/bold cyan] - {group['description']}")
                    for realm in group.get("realms", []):
                        realm_list.append(realm)
                        is_nsfw = realm.get("is_nsfw", False)
                        nsfw_tag = " [red][18+][/red]" if is_nsfw else ""
                        console.print(f"  [{realm['id'][:8]}] [bold]{realm['name']}[/bold]{nsfw_tag}")
                        if realm.get("tagline"):
                            console.print(f"           [dim]{realm['tagline']}[/dim]")
                return
        except Exception as e:
            print_error(f"Failed to list realms: {e}")
            raise typer.Exit(1)

    # Flat list (with --land filter)
    table = Table(title=f"Realms in {land}" if land else "Realms")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Tagline")
    table.add_column("Players", justify="right")

    for realm in realm_list:
        table.add_row(
            realm["id"][:8],
            realm["name"],
            realm.get("tagline", ""),
            str(realm.get("player_count", 0)),
        )

    console.print(table)


# Keep "worlds" as alias for backwards compatibility
@app.command(hidden=True)
def worlds(
    realm: Optional[str] = typer.Option(None, "--realm", "-r", help="Filter by land"),
    nsfw: bool = typer.Option(False, "--nsfw", help="Include 18+ realms"),
):
    """Alias for 'realms' command."""
    realms(land=realm, nsfw=nsfw)


@app.command()
def lands():
    """
    List available lands (genre categories).

    Pick a land to start your adventure!
    """
    with get_client() as client:
        try:
            groups = client.list_worlds_grouped()

            console.print("\n[bold]Choose your adventure:[/bold]\n")

            for i, group in enumerate(groups, 1):
                is_locked = group.get("is_locked", False)
                realm_count = group.get("realm_count", 0)

                if is_locked:
                    console.print(f"  [dim]{i}. {group['display_name']} ({realm_count} realms) [18+][/dim]")
                else:
                    console.print(f"  [cyan]{i}.[/cyan] [bold]{group['display_name']}[/bold] - {group.get('description', '')}")
                    console.print(f"     [dim]{realm_count} realms available[/dim]")

            console.print("\n[dim]To play: textlands play[/dim]")
            console.print("[dim]To see realms in a land: textlands realms --land fantasy[/dim]")

        except Exception as e:
            print_error(f"Failed to list lands: {e}")
            raise typer.Exit(1)


@app.command()
def play(
    realm: Optional[str] = typer.Argument(None, help="Realm ID or name to play in"),
):
    """
    Start playing TextLands.

    If no realm is specified, shows realm selection.
    """
    with get_client() as client:
        # Check for existing session
        current = get_current_session()
        if current and current.get("realm_id") and not realm:
            resume = Prompt.ask(
                f"Resume your adventure in [bold]{current.get('realm_name', 'unknown')}[/bold] as [bold]{current.get('character_name', 'unknown')}[/bold]?",
                choices=["y", "n"],
                default="y",
            )
            if resume == "y":
                _game_loop(client)
                return

        # Select realm
        if not realm:
            realm = _select_realm(client)
            if not realm:
                return

        # Get campfire (character selection)
        try:
            campfire = client.get_campfire(realm)  # API param still world_id
        except Exception as e:
            print_error(f"Failed to load realm: {e}")
            raise typer.Exit(1)

        # Display campfire scene
        console.print(f"\n[bold cyan]{campfire['world_name']}[/bold cyan]")  # API field still world_name
        if campfire.get("world_tagline"):
            console.print(f"[italic]{campfire['world_tagline']}[/italic]")
        console.print()
        console.print(Panel(campfire["intro_text"], title="The Journey Begins", padding=(1, 2)))

        # Character selection
        entity_id = _select_character(client, realm, campfire)
        if not entity_id:
            return

        # Start session
        try:
            result = client.start_session(realm, entity_id)  # API param still world_id
        except Exception as e:
            print_error(f"Failed to start session: {e}")
            raise typer.Exit(1)

        # Store session
        session = result.get("session", {})
        set_current_session({
            "realm_id": session.get("world_id"),  # API field still world_id
            "realm_name": session.get("world_name"),  # API field still world_name
            "character_id": session.get("character_id"),
            "character_name": session.get("character_name"),
        })

        # Show opening narrative
        console.print()
        print_success(result.get("message", "Your adventure begins..."))
        if result.get("opening_narrative"):
            console.print()
            print_narrative(result["opening_narrative"])

        # Enter game loop
        _game_loop(client)


def _select_realm(client: TextLandsClient) -> Optional[str]:
    """Interactive realm selection."""
    try:
        groups = client.list_worlds_grouped()  # No more include_nsfw param
    except Exception as e:
        print_error(f"Failed to list realms: {e}")
        return None

    # Flatten into numbered list
    all_realms = []
    console.print("\n[bold]Choose a realm:[/bold]\n")

    idx = 1
    for group in groups:
        if group.get("is_locked"):
            continue
        console.print(f"[bold cyan]{group['display_name']}[/bold cyan] - {group['description']}")
        # Use new field name: realms (not worlds)
        for realm in group.get("realms", []):
            all_realms.append(realm)
            console.print(f"  [cyan]{idx}.[/cyan] {realm['name']}")
            if realm.get("tagline"):
                console.print(f"      [dim]{realm['tagline']}[/dim]")
            idx += 1
        console.print()

    if not all_realms:
        print_error("No realms available")
        return None

    choice = IntPrompt.ask("Enter number", default=1)
    if choice < 1 or choice > len(all_realms):
        print_error("Invalid choice")
        return None

    return all_realms[choice - 1]["id"]


def _select_character(
    client: TextLandsClient,
    world_id: str,
    campfire: dict,
) -> Optional[str]:
    """Interactive character selection."""
    characters = campfire.get("characters", [])

    console.print("\n[bold]Choose your character:[/bold]\n")

    for i, char in enumerate(characters, 1):
        console.print(f"[cyan]{i}.[/cyan] [bold]{char['name']}[/bold]")
        if char.get("occupation"):
            console.print(f"    {char['occupation']}")
        if char.get("physical_summary"):
            console.print(f"    [dim]{char['physical_summary']}[/dim]")
        if char.get("backstory_hook"):
            console.print(f"    [italic]{char['backstory_hook']}[/italic]")
        console.print()

    if campfire.get("can_create_custom"):
        console.print(f"[cyan]{len(characters) + 1}.[/cyan] [bold]Create your own character[/bold]")
        console.print()

    choice = IntPrompt.ask("Enter number", default=1)

    # Custom character
    if campfire.get("can_create_custom") and choice == len(characters) + 1:
        concept = Prompt.ask("Describe your character")
        if not concept:
            return None
        try:
            result = client.create_custom_character(world_id, concept)
            return result.get("id")
        except Exception as e:
            print_error(f"Failed to create character: {e}")
            return None

    if choice < 1 or choice > len(characters):
        print_error("Invalid choice")
        return None

    return characters[choice - 1]["id"]


# =========== Natural Language Chat Parsing ===========

def _parse_dm_intent(text: str) -> Optional[tuple[str, str]]:
    """Parse natural language DM intent. Returns (recipient, message) or None."""
    text_lower = text.lower().strip()

    patterns = [
        r"^(?:dm|message|msg|whisper|pm)\s+(\w+)\s+(.+)$",
        r"^tell\s+(\w+)\s+(?:that\s+)?(.+)$",
        r"^send\s+(?:a\s+)?(?:message|dm|pm)\s+to\s+(\w+)\s+(?:saying\s+)?(.+)$",
        r"^(?:message|dm|pm)\s+(\w+)\s+(?:and\s+)?(?:say|tell\s+them)\s+(.+)$",
        r"^let\s+(\w+)\s+know\s+(?:that\s+)?(.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text_lower)
        if match:
            recipient = match.group(1)
            msg_start = text_lower.find(match.group(2))
            message = text[msg_start:] if msg_start > 0 else match.group(2)
            return (recipient, message)
    return None


def _parse_inbox_intent(text: str) -> bool:
    """Check if user wants to see their messages."""
    text_lower = text.lower().strip()
    inbox_phrases = [
        "inbox", "messages", "mail", "dms", "check messages", "check my messages",
        "any messages", "do i have messages", "who messaged me", "who wrote me",
        "show messages", "read messages", "unread", "my inbox"
    ]
    return any(phrase in text_lower for phrase in inbox_phrases)


def _parse_global_chat_intent(text: str) -> Optional[str]:
    """Parse intent to send global chat. Returns message or None."""
    text_lower = text.lower().strip()

    patterns = [
        r"^global\s+(.+)$",
        r"^(?:say|tell|broadcast|shout)\s+(?:to\s+)?(?:everyone|all|everybody|the world)\s*[:\-]?\s*(.+)$",
        r"^(?:to\s+)?(?:everyone|all|everybody)[:\-]?\s+(.+)$",
    ]

    for pattern in patterns:
        match = re.match(pattern, text_lower)
        if match:
            msg_start = text_lower.find(match.group(1))
            return text[msg_start:] if msg_start > 0 else match.group(1)
    return None


def _handle_chat_intent(client: TextLandsClient, action: str) -> bool:
    """Handle chat-related natural language. Returns True if handled."""
    # Check for DM intent
    dm_intent = _parse_dm_intent(action)
    if dm_intent:
        recipient, message = dm_intent
        try:
            result = client.send_dm(recipient, message)
            if result.get("success"):
                print_success(f"Message sent to {recipient}")
            else:
                print_error(result.get("error", "Failed to send message"))
        except Exception as e:
            print_error(f"Failed to send: {e}")
        return True

    # Check for inbox intent
    if _parse_inbox_intent(action):
        _show_messages(client)
        return True

    # Check for global chat intent
    global_msg = _parse_global_chat_intent(action)
    if global_msg:
        try:
            result = client.send_global_chat(global_msg)
            if result.get("success"):
                print_success("Sent to global chat")
            else:
                print_error(result.get("error", "Failed to send"))
        except Exception as e:
            print_error(f"Failed to send: {e}")
        return True

    return False


def _show_messages(client: TextLandsClient) -> None:
    """Show pending messages."""
    try:
        result = client.get_pending_messages()
        messages = result.get("messages", [])

        if not messages:
            console.print("[dim]No unread messages. Your inbox is empty.[/dim]")
            return

        console.print(f"\n[bold cyan]📬 {len(messages)} Message(s):[/bold cyan]\n")
        for msg in messages[:10]:
            sender = msg.get("sender_name", msg.get("sender_id", "Unknown"))
            content = msg.get("content", "")
            console.print(f"[bold]{sender}[/bold]: {content}\n")

        if len(messages) > 10:
            console.print(f"[dim]...and {len(messages) - 10} more[/dim]")

        console.print('[dim]Reply: "message <name> <your reply>"[/dim]')
    except Exception as e:
        print_error(f"Failed to load messages: {e}")


def _show_chat(client: TextLandsClient) -> None:
    """Show recent global chat."""
    try:
        result = client.get_global_chat(limit=10)
        messages = result.get("messages", [])

        if not messages:
            console.print("[dim]No recent chat messages.[/dim]")
            return

        console.print("\n[bold cyan]🌍 Recent Global Chat:[/bold cyan]\n")
        for msg in reversed(messages):  # Show oldest first
            sender = msg.get("sender_name", "Unknown")
            content = msg.get("message", "")
            console.print(f"[bold]{sender}[/bold]: {content}")
        console.print()
    except Exception as e:
        print_error(f"Failed to load chat: {e}")


def _game_loop(client: TextLandsClient) -> None:
    """Main game loop."""
    console.print("\n[dim]Type your actions naturally. /help for commands.[/dim]\n")

    # Show unread count on start
    try:
        unread = client.get_unread_count()
        if unread > 0:
            console.print(f"[yellow]📬 You have {unread} unread message(s). Type \"messages\" to read.[/yellow]\n")
    except:
        pass

    while True:
        try:
            action = Prompt.ask("[bold]>[/bold]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n")
            break

        if not action:
            continue

        action_lower = action.lower().strip()

        # Handle slash commands
        if action_lower in ("/quit", "/exit", "/q"):
            print_success("Farewell, adventurer!")
            break

        if action_lower in ("/look", "/l"):
            _do_look(client)
            continue

        if action_lower in ("/inventory", "/inv", "/i"):
            _do_inventory(client)
            continue

        if action_lower in ("/rest", "/r"):
            _do_rest(client)
            continue

        if action_lower in ("/messages", "/m", "/inbox"):
            _show_messages(client)
            continue

        if action_lower in ("/chat", "/c"):
            _show_chat(client)
            continue

        if action_lower in ("/help", "/h", "/?"):
            _show_help()
            continue

        if action_lower.startswith("/"):
            print_error(f"Unknown command: {action}")
            continue

        # Check for chat intent (natural language)
        if _handle_chat_intent(client, action):
            continue

        # Regular game action
        _do_action(client, action)


def _do_action(client: TextLandsClient, action: str) -> None:
    """Execute a game action."""
    try:
        result = client.do_action(action)
    except Exception as e:
        print_error(f"Action failed: {e}")
        return

    if result.get("error"):
        print_error(result["error"])
        return

    # Print narrative
    narrative = result.get("narrative", "")
    mood = result.get("mood", "neutral")
    print_narrative(narrative, mood)

    # Print suggestions
    print_suggestions(result.get("suggested_actions", []))

    # Handle account prompts for guests
    if result.get("requires_account"):
        console.print(f"\n[yellow]{result.get('account_prompt_incentive', 'Sign up to continue!')}[/yellow]")
        console.print("[dim]Visit https://textlands.com to create an account[/dim]")


def _do_look(client: TextLandsClient) -> None:
    """Look around."""
    try:
        result = client.look()
    except Exception as e:
        print_error(f"Failed: {e}")
        return

    print_narrative(result.get("narrative", "You look around..."))
    print_suggestions(result.get("suggested_actions", []))


def _do_inventory(client: TextLandsClient) -> None:
    """Check inventory."""
    try:
        result = client.inventory()
    except Exception as e:
        print_error(f"Failed: {e}")
        return

    print_narrative(result.get("narrative", "You check your belongings..."))


def _do_rest(client: TextLandsClient) -> None:
    """Rest and recover."""
    try:
        result = client.rest()
    except Exception as e:
        print_error(f"Failed: {e}")
        return

    print_narrative(result.get("narrative", "You rest for a while..."))


def _show_help() -> None:
    """Show help."""
    help_text = """
## Commands

- `/look` or `/l` - Look around your current location
- `/inventory` or `/i` - Check your inventory
- `/rest` or `/r` - Rest and recover
- `/messages` or `/m` - Check your messages
- `/chat` - View recent chat
- `/quit` or `/q` - Exit the game

## Actions

Just type what you want to do in natural language:
- "search the room"
- "talk to the bartender"
- "attack the goblin"

## Chat

Talk to other players naturally:
- "message Kira I found the treasure"
- "tell everyone hello"
- "check my messages"
- "who messaged me"

Your progress is saved automatically.
"""
    console.print(Markdown(help_text))


@app.command()
def config(
    api_url: Optional[str] = typer.Option(None, "--api-url", help="Set API URL"),
    show: bool = typer.Option(False, "--show", help="Show current config"),
):
    """Configure CLI settings."""
    if show:
        console.print(f"API URL: {get_api_url()}")
        console.print(f"Authenticated: {'Yes' if is_authenticated() else 'No'}")
        if guest_id := get_guest_id():
            console.print(f"Guest ID: {guest_id}")
        return

    if api_url:
        set_api_url(api_url)
        print_success(f"API URL set to {api_url}")


if __name__ == "__main__":
    app()
