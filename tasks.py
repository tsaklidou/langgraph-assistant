from invoke import task

@task
def setup(c):
    """Install dependencies and setup environment"""
    print("Installing dependencies...")
    c.run("pip install -r requirements.txt")
    c.run("cp .env.example .env", warn=True)
    print("Setup complete! Edit .env with your API keys")

@task
def process(c):
    """Process data and create vector database"""
    print("Processing data...")
    c.run("cd src && python preprocessing/main.py")
    print("Data processing complete!")

@task
def run(c):
    """Start the application"""
    print("Starting app...")
    c.run("cd src && streamlit run app/ui_app.py")

@task
def test(c):
    """Run tests"""
    print("Running tests...")
    c.run("pytest tests/ -v")

@task
def clean(c):
    """Clean up generated files"""
    print("Cleaning up...")
    c.run("rm -rf src/chroma_db/ *.db src/__pycache__ tests/__pycache__", warn=True)

@task(setup, process)
def all(c):
    """Setup everything and prepare to run"""
    print("Ready to run! Use 'invoke run' to start the app")