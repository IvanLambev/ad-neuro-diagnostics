from __future__ import annotations

from pathlib import Path

import typer

from .experiments import fit_models
from .features import extract_all_features
from .inference import run_tribe_batch
from .ingest import export_ratings_template, import_ratings, normalize_ads, register_ads
from .manifests import init_project, load_paths
from .reports import generate_compare_report, generate_single_report

app = typer.Typer(help="Brain-inspired creative diagnostics for short video ads.")
ingest_app = typer.Typer(help="Project and asset ingest commands.")
annotate_app = typer.Typer(help="Annotation template and import commands.")
report_app = typer.Typer(help="Generate reports from cached artifacts.")

app.add_typer(ingest_app, name="ingest")
app.add_typer(annotate_app, name="annotate")
app.add_typer(report_app, name="report")


@ingest_app.command("init")
def ingest_init(project_root: Path = typer.Option(..., dir_okay=True, file_okay=False)) -> None:
    init_project(project_root)
    typer.echo(f"Initialized project at {project_root}")


@ingest_app.command("register")
def ingest_register(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    input_csv: Path = typer.Option(..., exists=True, dir_okay=False),
) -> None:
    paths = load_paths(project_root)
    merged = register_ads(paths, input_csv)
    typer.echo(f"Registered {len(merged)} ads")


@ingest_app.command("normalize")
def ingest_normalize(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    ffmpeg_bin: str = typer.Option("ffmpeg"),
    ffprobe_bin: str = typer.Option("ffprobe"),
    width: int = typer.Option(1280),
    height: int = typer.Option(720),
    fps: int = typer.Option(30),
) -> None:
    paths = load_paths(project_root)
    clips = normalize_ads(
        paths,
        ffmpeg_bin=ffmpeg_bin,
        ffprobe_bin=ffprobe_bin,
        width=width,
        height=height,
        fps=fps,
    )
    typer.echo(f"Normalized {len(clips)} clips")


@annotate_app.command("export")
def annotate_export(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    annotators: int = typer.Option(3, min=1),
    output: Path | None = typer.Option(None),
) -> None:
    paths = load_paths(project_root)
    out = export_ratings_template(paths, annotators=annotators, output=output)
    typer.echo(f"Wrote ratings template to {out}")


@annotate_app.command("import")
def annotate_import(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    ratings_csv: Path = typer.Option(..., exists=True, dir_okay=False),
) -> None:
    paths = load_paths(project_root)
    frame = import_ratings(paths, ratings_csv)
    typer.echo(f"Imported {len(frame)} rating rows")


@app.command("run-tribe")
def run_tribe(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    tribe_repo: Path | None = typer.Option(None, exists=True, file_okay=False),
    python_exe: str = typer.Option("python"),
    device: str = typer.Option("cuda"),
    force: bool = typer.Option(False),
) -> None:
    paths = load_paths(project_root)
    result = run_tribe_batch(
        paths, tribe_repo=tribe_repo, python_exe=python_exe, device=device, force=force
    )
    typer.echo(result.to_string(index=False) if not result.empty else "No clips processed")


@app.command("extract-features")
def extract_features_cmd(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    top_k: int = typer.Option(10, min=1),
    fps: float = typer.Option(1.0, gt=0.0),
) -> None:
    paths = load_paths(project_root)
    frame = extract_all_features(paths, top_k=top_k, fps=fps)
    typer.echo(f"Extracted features for {len(frame)} ads")


@app.command("train-baseline")
def train_baseline(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    group_by: str = typer.Option("campaign"),
) -> None:
    paths = load_paths(project_root)
    out_dir = fit_models(paths, group_by=group_by)
    typer.echo(f"Wrote experiment outputs to {out_dir}")


@report_app.command("single")
def report_single(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    ad_id: str = typer.Option(...),
) -> None:
    paths = load_paths(project_root)
    report_path = generate_single_report(paths, ad_id)
    typer.echo(f"Wrote report to {report_path}")


@report_app.command("compare")
def report_compare(
    project_root: Path = typer.Option(..., dir_okay=True, file_okay=False),
    ad_a: str = typer.Option(...),
    ad_b: str = typer.Option(...),
) -> None:
    paths = load_paths(project_root)
    report_path = generate_compare_report(paths, ad_a, ad_b)
    typer.echo(f"Wrote report to {report_path}")
