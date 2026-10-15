import pytest

from cityomics import privacy
from cityomics.paths import REPO_ROOT


def test_repository_has_no_secrets():
    findings = privacy.scan_repo(REPO_ROOT)
    assert not findings, "\n".join(map(str, findings))


def test_detects_planted_secret(tmp_path):
    # Montado em tempo de execução para que o próprio teste não dispare a varredura do repo.
    fake = "sk-or-v1-" + "a1" * 20
    (tmp_path / "notebook.py").write_text(f'KEY = "{fake}"\n')
    (tmp_path / ".env").write_text(f"OPENROUTER_API_KEY={fake}\n")  # .env é ignorado
    findings = privacy.scan_repo(tmp_path)
    assert [f.path.name for f in findings] == ["notebook.py"]


def test_detects_forbidden_csv_column(tmp_path):
    (tmp_path / "setor_mes.csv").write_text("cd_setor,mes,LATITUDE,n\n1,2025-01,-23.5,3\n")
    (tmp_path / "ok.csv").write_text("cd_setor,mes,n\n1,2025-01,3\n")
    findings = privacy.scan_tables(tmp_path)
    assert len(findings) == 1 and "LATITUDE" in findings[0].detail


def test_detects_forbidden_parquet_column(tmp_path):
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    pq.write_table(pa.table({"num_bo": ["1"], "n": [1]}), tmp_path / "x.parquet")
    findings = privacy.scan_tables(tmp_path)
    assert len(findings) == 1 and findings[0].detail == "num_bo"


def test_processed_dir_is_clean():
    findings = privacy.scan_tables()
    assert not findings, "\n".join(map(str, findings))


def test_no_large_tracked_files():
    import subprocess

    files = subprocess.run(["git", "ls-files", "-z"], cwd=REPO_ROOT, capture_output=True, text=True).stdout
    big = [f for f in files.split("\0") if f and (REPO_ROOT / f).exists()
           and (REPO_ROOT / f).stat().st_size > 10_000_000]
    assert not big, f"arquivos versionados com mais de 10 MB: {big}"
