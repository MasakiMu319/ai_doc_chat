import logfire
from conf import settings

logfire.configure(token=settings.log.LOGFIRE_TOKEN, console=False)
logfire.install_auto_tracing(
    modules=["core", "service", "web", "main"],
    min_duration=0.0001,
    check_imported_modules="warn",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9527,
        reload=True,
    )
