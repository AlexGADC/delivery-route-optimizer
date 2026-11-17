from app.cli import main


def test_algorithms_lists_what_is_available(capsys):
    exit_code = main(["algorithms"])

    assert exit_code == 0
    assert "brute-force" in capsys.readouterr().out.splitlines()


def test_solve_prints_the_route_and_its_metrics(brasov5_path, capsys):
    exit_code = main(["solve", str(brasov5_path), "--algorithm", "brute-force"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "brasov-5 (4 customers)" in output
    assert "Coresi Mall" in output
    assert "Piața Sfatului" in output
    assert "Late stops    0 of 4" in output


def test_service_time_can_be_changed_from_the_command_line(brasov5_path, capsys):
    main(["solve", str(brasov5_path), "--algorithm", "brute-force", "--service-minutes", "0"])
    without_service = capsys.readouterr().out

    main(["solve", str(brasov5_path), "--algorithm", "brute-force", "--service-minutes", "20"])
    with_long_service = capsys.readouterr().out

    # Longer service means later arrivals, so the two reports cannot be identical.
    assert _table(without_service) != _table(with_long_service)


def _table(report: str) -> list[str]:
    """The lines of the route table, without the run time (which changes every run)."""
    return [line for line in report.splitlines() if not line.startswith("Algorithm")]
