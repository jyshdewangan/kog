import typer
from rich import print
from kog.core.session import session_manager
from kog.core.context import context_manager
from kog.agent.react_agent import create_agent_executor
from kog.agent.tools import SummarizeTool, MailTool
from langchain_core.messages import HumanMessage

app = typer.Typer(help="kog - Context-Aware CLI AI Agent")

def _ensure_session():
    current = session_manager.get_current_session()
    if not current:
        session_manager.create_session("default", set_as_current=True)
        return "default"
    return current

@app.command()
def open(file_path: str):
    """Opens a file, makes a context in the current session"""
    session = _ensure_session()
    try:
        context_name = context_manager.add_context(file_path)
        session_manager.add_context_to_session(session, context_name)
        print(f"[green]Successfully loaded '{file_path}' as context '{context_name}' into session '{session}'.[/green]")
    except Exception as e:
        print(f"[red]Error opening file: {e}[/red]")

@app.command()
def summarize():
    """Summarize based on the input context."""
    tool = SummarizeTool()
    print("[yellow]Generating summary...[/yellow]")
    result = tool._run()
    if result.startswith("Error"):
        print(f"[red]{result}[/red]")
    else:
        print(f"[bold cyan]Summary:[/bold cyan]\n{result}")

@app.command()
def ask(question: str):
    """Give answer based on context loaded"""
    from kog.agent.tools import AskTool
    tool = AskTool()
    print("[yellow]Thinking...[/yellow]")
    result = tool._run(question)
    if result.startswith("Error"):
        print(f"[red]{result}[/red]")
    else:
        print(f"[bold cyan]Answer:[/bold cyan]\n{result}")

@app.command()
def mail(to: str = typer.Option(..., "--to", help="Recipient email"), 
         mode: str = typer.Option(..., "--mode", help="Mail mode, e.g., summarize")):
    """Mail using smtp the required summary of the context"""
    if mode != "summarize":
        print(f"[red]Unsupported mode: {mode}. Only 'summarize' is supported.[/red]")
        raise typer.Exit()
        
    print("[yellow]Generating summary for email...[/yellow]")
    tool = SummarizeTool()
    summary = tool._run()
    if summary.startswith("Error"):
        print(f"[red]{summary}[/red]")
        raise typer.Exit()
        
    print(f"[yellow]Sending email to {to}...[/yellow]")
    mail_tool = MailTool()
    result = mail_tool._run(to_email=to, subject="Context Summary", body=summary)
    if result.startswith("Failed"):
        print(f"[red]{result}[/red]")
    else:
        print(f"[green]{result}[/green]")

@app.command(name="list-context")
def list_context():
    """List all the stored context"""
    contexts = context_manager.list_contexts()
    if not contexts:
        print("[yellow]No contexts stored.[/yellow]")
        return
    print("[bold]Stored Contexts:[/bold]")
    for name, data in contexts.items():
        print(f"- [cyan]{name}[/cyan] (Source: {data.get('source')})")

@app.command(name="load-context")
def load_context(ctx_name: str):
    """Loads a already stored context in current session"""
    session = _ensure_session()
    # Check if context exists
    contexts = context_manager.list_contexts()
    if ctx_name not in contexts:
        print(f"[red]Context '{ctx_name}' does not exist.[/red]")
        return
        
    session_manager.add_context_to_session(session, ctx_name)
    print(f"[green]Loaded context '{ctx_name}' into session '{session}'.[/green]")

@app.command(name="unload-context")
def unload_context(ctx_name: str):
    """Unload a context from the current session without deleting it globally"""
    session = _ensure_session()
    if session_manager.remove_context_from_session(session, ctx_name):
        print(f"[green]Unloaded context '{ctx_name}' from session '{session}'.[/green]")
    else:
        print(f"[yellow]Context '{ctx_name}' is not loaded in session '{session}'.[/yellow]")

@app.command(name="delete-context")
def delete_context(ctx_name: str):
    """delete the context from the context storage"""
    deleted_from_db = context_manager.delete_context(ctx_name)
    session_manager.remove_context_from_all_sessions(ctx_name)
    
    if deleted_from_db:
        print(f"[green]Deleted context '{ctx_name}'.[/green]")
    else:
        print(f"[yellow]Context '{ctx_name}' not found in storage, but cleaned from sessions.[/yellow]")

@app.command(name="list-sessions")
def list_sessions():
    """Lists all sessions"""
    sessions = session_manager.list_sessions()
    current = session_manager.get_current_session()
    
    if not sessions:
        print("[yellow]No sessions stored.[/yellow]")
        return
        
    print("[bold]Stored Sessions:[/bold]")
    for name, data in sessions.items():
        marker = "*" if name == current else " "
        ctx_count = len(data.get('contexts', []))
        print(f"{marker} [cyan]{name}[/cyan] ({ctx_count} contexts)")

@app.command(name="load-session")
def load_session(session_name: str):
    """Load a particular session. Asks for saving current if needed."""
    current = session_manager.get_current_session()
    if current and current == "default":
        # Ask to save
        save = typer.confirm(f"Do you want to save the current 'default' session with a new name before loading '{session_name}'?")
        if save:
            new_name = typer.prompt("Enter new session name")
            # rename session by creating new and moving data
            session_manager.create_session(new_name, set_as_current=False)
            contexts = session_manager.get_session_contexts("default")
            for c in contexts:
                session_manager.add_context_to_session(new_name, c)
            session_manager.delete_session("default")
            
    if session_manager.load_session(session_name):
        if session_name != current:
            print(f"[green]Loaded session '{session_name}'.[/green]")
    else:
        print(f"[yellow]Session '{session_name}' not found. Creating a new one.[/yellow]")
        session_manager.create_session(session_name, set_as_current=True)

@app.command(name="new-session")
def new_session(session_name: str):
    """Start a new session. Asks for saving current if it is unsaved."""
    current = session_manager.get_current_session()
    if current == session_name:
        print(f"[yellow]Session '{session_name}' is already the current session.[/yellow]")
        return
        
    if current and current == "default":
        # Ask to save
        save = typer.confirm(f"Do you want to save the current 'default' session with a new name before creating '{session_name}'?")
        if save:
            new_name = typer.prompt("Enter new session name")
            session_manager.create_session(new_name, set_as_current=False)
            contexts = session_manager.get_session_contexts("default")
            for c in contexts:
                session_manager.add_context_to_session(new_name, c)
            session_manager.delete_session("default")
            
    sessions = session_manager.list_sessions()
    if session_name in sessions:
        print(f"[yellow]Session '{session_name}' already exists. Use 'kog load_session {session_name}' to load it.[/yellow]")
        return
        
    session_manager.create_session(session_name, set_as_current=True)
    print(f"[green]Started new session '{session_name}'.[/green]")

@app.command(name="delete-session")
def delete_session(session_name: str):
    """Delete a particular session"""
    if session_manager.delete_session(session_name):
        print(f"[green]Deleted session '{session_name}'.[/green]")
    else:
        print(f"[red]Session '{session_name}' not found.[/red]")

@app.command()
def task(prompt: str):
    """Agentic loops for task execution in NLP"""
    _ensure_session()
    print(f"[bold magenta]Starting Agent Task:[/bold magenta] {prompt}")
    agent = create_agent_executor()
    try:
        inputs = {"messages": [HumanMessage(content=prompt)]}
        for chunk in agent.stream(inputs, stream_mode="values"):
            message = chunk["messages"][-1]
            if message.content:
                print(f"[cyan]{message.type}[/cyan]: {message.content}")
            if getattr(message, "tool_calls", None):
                for tc in message.tool_calls:
                    print(f"[yellow]Calling Tool:[/yellow] {tc['name']} with args {tc['args']}")
    except Exception as e:
        print(f"[red]Error during task execution: {e}[/red]")

@app.command()
def ps():
    """Display the current loaded session and loaded contexts in that session"""
    current = session_manager.get_current_session()
    if not current:
        print("[yellow]No active session.[/yellow]")
        return
        
    contexts = session_manager.get_session_contexts(current)
    print(f"[bold]Current Session:[/bold] [cyan]{current}[/cyan]")
    if contexts:
        print("[bold]Loaded Contexts:[/bold]")
        for c in contexts:
            print(f"  - {c}")
    else:
        print("  [No contexts loaded]")

@app.command(name="dev-reset", hidden=True)
def dev_reset():
    """[DEV] Reset all session and context data to start fresh."""
    import os
    import shutil
    from kog.core.config import config
    
    confirm = typer.confirm("Are you sure you want to delete ALL sessions and contexts? This cannot be undone.")
    if not confirm:
        print("[yellow]Reset cancelled.[/yellow]")
        return
        
    try:
        if os.path.exists(config.sessions_file):
            os.remove(config.sessions_file)
        if os.path.exists(config.contexts_file):
            os.remove(config.contexts_file)
        if os.path.exists(config.chroma_dir):
            shutil.rmtree(config.chroma_dir)
            
        print("[bold green]Successfully reset all local Kog data! You have a clean slate.[/bold green]")
    except Exception as e:
        print(f"[bold red]Failed to reset data: {e}[/bold red]")

if __name__ == "__main__":
    app()
