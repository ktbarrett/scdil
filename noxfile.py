import nox


@nox.session(reuse_venv=True)
def dev(session: nox.Session) -> None:
    session.install("-r", ".check-reqs.txt")
    session.install("-r", ".test-reqs.txt")
    session.install("-e", ".")
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
        "pytest", "--cov=scdil", "--cov-branch", "--doctest-modules", "src/", "tests/"
    )
    session.run("coverage", "xml")
