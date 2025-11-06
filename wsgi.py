"""
WSGI entry point for Gunicorn.
"""

from foodie import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
