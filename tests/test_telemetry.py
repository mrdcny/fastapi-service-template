from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def test_sqlalchemy_version_is_supported_by_instrumentation() -> None:
    # The instrumentor silently does nothing on unsupported versions, which would drop
    # every database span. This turns that into a test failure on dependency upgrades.
    assert SQLAlchemyInstrumentor()._check_dependency_conflicts() is None
