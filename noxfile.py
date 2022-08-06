import nox


@nox.session(reuse_venv=True)
def dev(session: nox.Session) -> None:
    session.install("-r", ".check-reqs.txt")
    session.install("-r", ".test-reqs.txt")
    session.install("-e", ".")
    if session.posargs:
        session.run(*session.posargs, external=True)
    else:
        session.run("bash", external=True)


@nox.session(reuse_venv=True)
def check(session: nox.Session) -> None:
    session.install("pre-commit")
    session.run("pre-commit", "run", "-a")


@nox.session
def tests(session: nox.Session) -> None:
    session.install("-r", ".test-reqs.txt")
    session.install(".")
    session.run(
        "pytest",
        "--cov=scdil",
        "--cov-branch",
        "tests/",
        *session.posargs,
    )
    session.run("coverage", "xml")
